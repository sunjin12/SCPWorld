/// API and configuration constants.
class AppConstants {
  AppConstants._();

  /// Backend API base URL (override for production)
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://scp-backend-1087559947666.asia-southeast1.run.app',
  );

  /// Google OAuth Client ID (public value, safe for client)
  static const String googleClientId = String.fromEnvironment(
    'GOOGLE_CLIENT_ID',
    defaultValue: '1087559947666-uuelrdfelo0c76nm837e4v9epv5er3sa.apps.googleusercontent.com',
  );

  /// SSE streaming endpoint
  static const String chatStreamEndpoint = '/api/chat/stream';
}
