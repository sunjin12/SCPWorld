import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../models/user.dart';
import '../config/constants.dart';

/// Auth state provider managing Google Sign-In (v7.x API).
final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() => const AuthState();

  /// Initialize Google Sign-In (call once at app startup).
  Future<void> initialize() async {
    // Initialize with Client ID from environment or constants
    await GoogleSignIn.instance.initialize(
      clientId: AppConstants.googleClientId,
    );

    // Listen for sign-in/sign-out events
    GoogleSignIn.instance.authenticationEvents.listen((event) {
      if (event is GoogleSignInAuthenticationEventSignIn) {
        _handleAccount(event.user);
      } else if (event is GoogleSignInAuthenticationEventSignOut) {
        state = const AuthState();
      }
    });

    // Try silent authentication (lightweight)
    try {
      final result = await GoogleSignIn.instance.attemptLightweightAuthentication();
      if (result != null) {
        await _handleAccount(result);
      }
    } catch (e) {
      // Slient auth failures can be ignored
    }
  }

  /// Perform Google Sign-In (Interactive)
  Future<void> signIn() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      // In web, authenticate() triggers the popup/redirect
      final account = await GoogleSignIn.instance.authenticate();
      await _handleAccount(account);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> _handleAccount(GoogleSignInAccount account) async {
    // Access idToken via authentication property
    final auth = account.authentication;
    final idToken = auth.idToken;

    if (idToken == null || idToken.isEmpty) {
      state = state.copyWith(isLoading: false, error: 'No ID token received');
      return;
    }

    final user = AppUser(
      userId: account.id,
      email: account.email,
      name: account.displayName ?? '',
      picture: account.photoUrl ?? '',
      idToken: idToken,
    );

    state = AuthState(user: user, isLoading: false);
  }

  /// Sign out.
  Future<void> signOut() async {
    await GoogleSignIn.instance.signOut();
    state = const AuthState();
  }
}
