"""Storage service — Firestore-based RAG vector search and session storage."""

from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure

from app.config import settings
from app.models.session import Message


class StorageService:
    """Unified storage service using Google Cloud Firestore (Native Mode)."""

    def __init__(self, db: firestore.Client):
        self.db = db
        self.doc_collection = settings.FIRESTORE_COLLECTION
        self.session_collection = settings.FIRESTORE_SESSION_COLLECTION

    # --- RAG: Vector Search ---

    async def vector_search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        item_number: str | None = None,
        object_class: str | None = None,
    ) -> list[dict]:
        """
        Perform vector similarity search using Firestore's find_nearest.
        """
        base_query = self.db.collection(self.doc_collection)

        # 1. Apply metadata filters if provided
        if item_number:
            base_query = base_query.where("item_number", "==", item_number)
        if object_class:
            base_query = base_query.where("object_class", "==", object_class)

        # 2. Execute vector search query
        # Requires a composite index to be READY for combined filters
        query = base_query.find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_vector),
            distance_measure=DistanceMeasure.COSINE,
            limit=top_k,
        )

        docs = query.get()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            # Remove embedding before returning to avoid large payload
            if "embedding" in data:
                del data["embedding"]
            results.append(data)
            
        return results

    # --- Session: Conversation History ---

    def _session_path(
        self, user_id: str, persona_id: str, session_id: str
    ) -> str:
        """Isolated path for session document, keyed per persona.

        Double-underscore separator distinguishes the new format from the
        legacy ``{user_id}_{session_id}`` keys so old and new documents
        can coexist without collision.
        """
        return f"{user_id}__{persona_id}__{session_id}"

    async def get_history(
        self, user_id: str, persona_id: str, session_id: str
    ) -> list[Message]:
        """Retrieve conversation history from Firestore sessions collection."""
        doc_ref = self.db.collection(self.session_collection).document(
            self._session_path(user_id, persona_id, session_id)
        )
        doc = doc_ref.get()

        if not doc.exists:
            return []

        data = doc.to_dict()
        messages = data.get("messages", [])
        return [Message(**m) for m in messages]

    async def save_history(
        self,
        user_id: str,
        persona_id: str,
        session_id: str,
        messages: list[Message],
    ):
        """Persist conversation history."""
        doc_ref = self.db.collection(self.session_collection).document(
            self._session_path(user_id, persona_id, session_id)
        )

        doc_ref.set({
            "messages": [m.model_dump() for m in messages],
            "updated_at": firestore.SERVER_TIMESTAMP,
            "user_id": user_id,
            "persona_id": persona_id,
            "session_id": session_id,
        })

    async def clear_session(
        self, user_id: str, persona_id: str, session_id: str
    ):
        """Delete session history."""
        self.db.collection(self.session_collection).document(
            self._session_path(user_id, persona_id, session_id)
        ).delete()

    # --- Auth: User Caching ---

    async def save_user(self, user: dict):
        """Cache verified user profile info."""
        user_id = user.get("user_id")
        if not user_id:
            return

        doc_ref = self.db.collection("users").document(user_id)
        doc_ref.set({
            **user,
            "last_login": firestore.SERVER_TIMESTAMP
        })
