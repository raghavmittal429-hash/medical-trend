import 'package:flutter/material.dart';

// ═══════════════════════════════════════════════════════════════
//  AROGYA PANDIT — Brand Theme
//  Derived from logo: Charcoal + Crimson + Blush
// ═══════════════════════════════════════════════════════════════

// ── Brand Color Palette ─────────────────────────────────────────
class APColors {
  APColors._();

  // Primary — Crimson Red (from logo)
  static const Color crimson900 = Color(0xFF5C0A0A);
  static const Color crimson800 = Color(0xFF7A1212);
  static const Color crimson700 = Color(0xFF8B1A1A);
  static const Color crimson600 = Color(0xFFA01A1A); // Primary brand red
  static const Color crimson500 = Color(0xFFB52020);
  static const Color crimson400 = Color(0xFFCB3535);
  static const Color crimson200 = Color(0xFFEEAAAA);
  static const Color crimson100 = Color(0xFFF7D4D4);
  static const Color crimson50  = Color(0xFFFDF0F0);

  // Secondary — Charcoal (from logo)
  static const Color charcoal900 = Color(0xFF1A1A1A);
  static const Color charcoal800 = Color(0xFF2B2B2B); // Logo dark
  static const Color charcoal700 = Color(0xFF3C3C3C);
  static const Color charcoal600 = Color(0xFF4E4E4E);
  static const Color charcoal400 = Color(0xFF717171);
  static const Color charcoal200 = Color(0xFFB5B5B5);
  static const Color charcoal100 = Color(0xFFDEDEDE);
  static const Color charcoal50  = Color(0xFFF5F5F5);

  // Accent — Blush (logo background)
  static const Color blush100 = Color(0xFFFAF0F0);
  static const Color blush200 = Color(0xFFF5E3E3);
  static const Color blush300 = Color(0xFFEDCCCC);

  // Semantic
  static const Color success  = Color(0xFF2E7D32);
  static const Color warning  = Color(0xFFE65100);
  static const Color info     = Color(0xFF1565C0);
  static const Color error    = Color(0xFFC62828);

  // Surfaces
  static const Color surface   = Color(0xFFFFFFFF);
  static const Color background = Color(0xFFFAF3F3); // Blush tinted bg
}

// ── Text Styles ──────────────────────────────────────────────────
class APTextStyles {
  APTextStyles._();

  static const TextStyle displayLarge = TextStyle(
    fontSize: 28,
    fontWeight: FontWeight.w700,
    color: APColors.charcoal900,
    letterSpacing: -0.5,
  );

  static const TextStyle headlineMedium = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w700,
    color: APColors.charcoal900,
    letterSpacing: -0.2,
  );

  static const TextStyle titleLarge = TextStyle(
    fontSize: 17,
    fontWeight: FontWeight.w600,
    color: APColors.charcoal800,
  );

  static const TextStyle titleMedium = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w600,
    color: APColors.charcoal800,
  );

  static const TextStyle bodyLarge = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w400,
    color: APColors.charcoal800,
    height: 1.5,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontSize: 13,
    fontWeight: FontWeight.w400,
    color: APColors.charcoal700,
    height: 1.45,
  );

  static const TextStyle labelSmall = TextStyle(
    fontSize: 11,
    fontWeight: FontWeight.w600,
    color: APColors.charcoal400,
    letterSpacing: 0.6,
  );

  static const TextStyle crimsonLabel = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w600,
    color: APColors.crimson600,
    letterSpacing: 0.3,
  );
}

// ── Spacing ──────────────────────────────────────────────────────
class APSpacing {
  APSpacing._();

  static const double xs  = 4.0;
  static const double sm  = 8.0;
  static const double md  = 12.0;
  static const double lg  = 16.0;
  static const double xl  = 24.0;
  static const double xxl = 32.0;
  static const double xxxl = 48.0;
}

// ── Border Radius ────────────────────────────────────────────────
class APRadius {
  APRadius._();

  static const double sm  = 6.0;
  static const double md  = 8.0;
  static const double lg  = 12.0;
  static const double xl  = 16.0;
  static const double pill = 100.0;
}

// ── Shadows ──────────────────────────────────────────────────────
class APShadows {
  APShadows._();

  static List<BoxShadow> get card => [
    BoxShadow(
      color: APColors.crimson600.withValues(alpha: 0.06),
      blurRadius: 12,
      offset: const Offset(0, 4),
    ),
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.04),
      blurRadius: 4,
      offset: const Offset(0, 1),
    ),
  ];

  static List<BoxShadow> get elevated => [
    BoxShadow(
      color: APColors.crimson600.withValues(alpha: 0.12),
      blurRadius: 20,
      offset: const Offset(0, 8),
    ),
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.06),
      blurRadius: 8,
      offset: const Offset(0, 2),
    ),
  ];
}

// ── Main Theme ───────────────────────────────────────────────────
class MediSimpleTheme {
  MediSimpleTheme._();

  static ThemeData get light => ThemeData(
    useMaterial3: true,
    fontFamily: 'Roboto',
    scaffoldBackgroundColor: APColors.background,

    colorScheme: const ColorScheme.light(
      primary: APColors.crimson600,
      onPrimary: Colors.white,
      primaryContainer: APColors.crimson50,
      onPrimaryContainer: APColors.crimson900,
      secondary: APColors.charcoal800,
      onSecondary: Colors.white,
      secondaryContainer: APColors.charcoal50,
      onSecondaryContainer: APColors.charcoal900,
      surface: APColors.surface,
      onSurface: APColors.charcoal900,
      error: APColors.error,
      onError: Colors.white,
    ),

    // ── AppBar ────────────────────────────────────────────────
    appBarTheme: const AppBarTheme(
      backgroundColor: APColors.charcoal900,
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w700,
        color: Colors.white,
        letterSpacing: -0.2,
      ),
      iconTheme: IconThemeData(color: Colors.white),
      actionsIconTheme: IconThemeData(color: Colors.white),
    ),

    // ── Cards ─────────────────────────────────────────────────
    cardTheme: CardThemeData(
      elevation: 0,
      color: APColors.surface,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(APRadius.lg),
        side: BorderSide(color: APColors.blush300, width: 1),
      ),
      margin: const EdgeInsets.only(bottom: APSpacing.md),
    ),

    // ── Elevated Button ───────────────────────────────────────
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: APColors.crimson600,
        foregroundColor: Colors.white,
        elevation: 0,
        shadowColor: Colors.transparent,
        padding: const EdgeInsets.symmetric(
          horizontal: APSpacing.xl,
          vertical: APSpacing.lg,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(APRadius.md),
        ),
        textStyle: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.2,
        ),
      ),
    ),

    // ── Outlined Button ───────────────────────────────────────
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: APColors.crimson600,
        side: const BorderSide(color: APColors.crimson600, width: 1.5),
        padding: const EdgeInsets.symmetric(
          horizontal: APSpacing.xl,
          vertical: APSpacing.lg,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(APRadius.md),
        ),
        textStyle: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),

    // ── Text Button ───────────────────────────────────────────
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: APColors.crimson600,
        textStyle: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),

    // ── Input / TextField ─────────────────────────────────────
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: APColors.surface,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: APSpacing.lg,
        vertical: APSpacing.md,
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(APRadius.md),
        borderSide: const BorderSide(color: APColors.blush300),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(APRadius.md),
        borderSide: const BorderSide(color: APColors.blush300),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(APRadius.md),
        borderSide: const BorderSide(color: APColors.crimson600, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(APRadius.md),
        borderSide: const BorderSide(color: APColors.error),
      ),
      hintStyle: const TextStyle(color: APColors.charcoal200, fontSize: 14),
      labelStyle: const TextStyle(color: APColors.charcoal600, fontSize: 14),
      floatingLabelStyle: const TextStyle(color: APColors.crimson600, fontSize: 12),
    ),

    // ── Bottom Navigation Bar ─────────────────────────────────
    navigationBarTheme: NavigationBarThemeData(
      height: 68,
      backgroundColor: APColors.surface,
      indicatorColor: APColors.crimson100,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 11,
          fontWeight: states.contains(WidgetState.selected)
              ? FontWeight.w700
              : FontWeight.w500,
          color: states.contains(WidgetState.selected)
              ? APColors.crimson700
              : APColors.charcoal400,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected)
              ? APColors.crimson700
              : APColors.charcoal400,
        ),
      ),
    ),

    // ── Chip ──────────────────────────────────────────────────
    chipTheme: ChipThemeData(
      backgroundColor: APColors.crimson50,
      selectedColor: APColors.crimson600,
      labelStyle: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w500,
        color: APColors.crimson800,
      ),
      side: const BorderSide(color: APColors.crimson200),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(APRadius.pill),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
    ),

    // ── Divider ───────────────────────────────────────────────
    dividerTheme: const DividerThemeData(
      color: APColors.blush300,
      thickness: 1,
      space: 1,
    ),

    // ── Dialog ────────────────────────────────────────────────
    dialogTheme: DialogThemeData(
      backgroundColor: APColors.surface,
      surfaceTintColor: Colors.transparent,
      elevation: 8,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(APRadius.xl),
      ),
      titleTextStyle: APTextStyles.headlineMedium,
      contentTextStyle: APTextStyles.bodyMedium,
    ),

    // ── SnackBar ──────────────────────────────────────────────
    snackBarTheme: SnackBarThemeData(
      backgroundColor: APColors.charcoal900,
      contentTextStyle: const TextStyle(color: Colors.white, fontSize: 14),
      actionTextColor: APColors.crimson200,
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(APRadius.md),
      ),
    ),

    // ── FloatingActionButton ──────────────────────────────────
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: APColors.crimson600,
      foregroundColor: Colors.white,
      elevation: 4,
      shape: CircleBorder(),
    ),

    // ── ListTile ──────────────────────────────────────────────
    listTileTheme: const ListTileThemeData(
      contentPadding: EdgeInsets.symmetric(horizontal: APSpacing.lg, vertical: APSpacing.xs),
      iconColor: APColors.crimson600,
      titleTextStyle: APTextStyles.bodyLarge,
      subtitleTextStyle: APTextStyles.bodyMedium,
    ),

    // ── Switch ────────────────────────────────────────────────
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? APColors.surface
            : APColors.charcoal200,
      ),
      trackColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? APColors.crimson600
            : APColors.blush300,
      ),
    ),

    // ── Checkbox ──────────────────────────────────────────────
    checkboxTheme: CheckboxThemeData(
      fillColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? APColors.crimson600
            : Colors.transparent,
      ),
      checkColor: WidgetStateProperty.all(Colors.white),
      side: const BorderSide(color: APColors.charcoal400, width: 1.5),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
    ),

    // ── Radio ─────────────────────────────────────────────────
    radioTheme: RadioThemeData(
      fillColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? APColors.crimson600
            : APColors.charcoal400,
      ),
    ),

    // ── Progress Indicator ────────────────────────────────────
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: APColors.crimson600,
      linearTrackColor: APColors.crimson100,
      circularTrackColor: APColors.crimson100,
    ),

    // ── Tab Bar ───────────────────────────────────────────────
    tabBarTheme: const TabBarThemeData(
      labelColor: APColors.crimson700,
      unselectedLabelColor: APColors.charcoal400,
      indicatorColor: APColors.crimson600,
      labelStyle: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
      unselectedLabelStyle: TextStyle(fontSize: 14, fontWeight: FontWeight.w400),
    ),

    // ── Tooltip ───────────────────────────────────────────────
    tooltipTheme: TooltipThemeData(
      decoration: BoxDecoration(
        color: APColors.charcoal900,
        borderRadius: BorderRadius.circular(APRadius.sm),
      ),
      textStyle: const TextStyle(color: Colors.white, fontSize: 12),
    ),
  );
}

// ── Reusable Widget Components ───────────────────────────────────

/// A branded card with optional accent border on the left
class APCard extends StatelessWidget {
  const APCard({
    super.key,
    required this.child,
    this.accent = false,
    this.padding,
    this.margin,
  });

  final Widget child;
  final bool accent;
  final EdgeInsets? padding;
  final EdgeInsets? margin;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin ?? const EdgeInsets.only(bottom: APSpacing.md),
      decoration: BoxDecoration(
        color: APColors.surface,
        borderRadius: BorderRadius.circular(APRadius.lg),
        border: Border(
          left: accent
              ? const BorderSide(color: APColors.crimson600, width: 3)
              : BorderSide.none,
          top: const BorderSide(color: APColors.blush300),
          right: const BorderSide(color: APColors.blush300),
          bottom: const BorderSide(color: APColors.blush300),
        ),
        boxShadow: APShadows.card,
      ),
      child: Padding(
        padding: padding ?? const EdgeInsets.all(APSpacing.lg),
        child: child,
      ),
    );
  }
}

/// A status pill badge (e.g. "Normal", "High", "Critical")
class APStatusBadge extends StatelessWidget {
  const APStatusBadge({
    super.key,
    required this.label,
    this.type = APBadgeType.neutral,
  });

  final String label;
  final APBadgeType type;

  @override
  Widget build(BuildContext context) {
    final (bg, fg) = switch (type) {
      APBadgeType.success  => (const Color(0xFFE8F5E9), const Color(0xFF1B5E20)),
      APBadgeType.warning  => (const Color(0xFFFFF3E0), const Color(0xFFBF360C)),
      APBadgeType.danger   => (APColors.crimson50, APColors.crimson800),
      APBadgeType.neutral  => (APColors.charcoal50, APColors.charcoal700),
      APBadgeType.primary  => (APColors.crimson50, APColors.crimson800),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(APRadius.pill),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: fg,
          letterSpacing: 0.3,
        ),
      ),
    );
  }
}

enum APBadgeType { success, warning, danger, neutral, primary }

/// A section header with optional trailing action
class APSectionHeader extends StatelessWidget {
  const APSectionHeader({
    super.key,
    required this.title,
    this.icon,
    this.trailing,
  });

  final String title;
  final IconData? icon;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: APSpacing.sm),
      child: Row(
        children: [
          if (icon != null) ...[
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: APColors.crimson50,
                borderRadius: BorderRadius.circular(APRadius.sm),
              ),
              child: Icon(icon, color: APColors.crimson600, size: 18),
            ),
            const SizedBox(width: APSpacing.sm),
          ],
          Expanded(
            child: Text(title, style: APTextStyles.headlineMedium),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}

/// A branded primary button with loading state
class APPrimaryButton extends StatelessWidget {
  const APPrimaryButton({
    super.key,
    required this.label,
    this.onPressed,
    this.icon,
    this.loading = false,
    this.fullWidth = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool loading;
  final bool fullWidth;

  @override
  Widget build(BuildContext context) {
    final btn = ElevatedButton(
      onPressed: loading ? null : onPressed,
      child: loading
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Colors.white,
              ),
            )
          : Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (icon != null) ...[
                  Icon(icon, size: 18),
                  const SizedBox(width: 8),
                ],
                Text(label),
              ],
            ),
    );
    return fullWidth ? SizedBox(width: double.infinity, child: btn) : btn;
  }
}

// ── How to use ───────────────────────────────────────────────────
//
//  In your main.dart MaterialApp:
//
//  MaterialApp(
//    title: 'MediSimple',
//    theme: MediSimpleTheme.light,
//    home: const HomePage(),
//  );
//
//  Then use brand tokens directly:
//
//  Color primary = APColors.crimson600;
//  double spacing = APSpacing.lg;
//  TextStyle title = APTextStyles.headlineMedium;
//
//  Widgets:
//  APCard(accent: true, child: ...)
//  APStatusBadge(label: 'Normal', type: APBadgeType.success)
//  APSectionHeader(title: 'Lab Results', icon: Icons.science)
//  APPrimaryButton(label: 'Upload Report', onPressed: ..., icon: Icons.upload)
