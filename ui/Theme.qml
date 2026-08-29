pragma Singleton
import QtQuick

QtObject {
    property bool darkMode: true

    // Dark palette
    readonly property color darkBackground: "#121212"
    readonly property color darkSurface: "#1E1E1E"
    readonly property color darkSurfaceAlt: "#2A2A2A"
    readonly property color darkText: "#F5F5F5"
    readonly property color darkTextMuted: "#A0A0A0"
    readonly property color darkBorder: "#3A3A3A"

    // Light palette
    readonly property color lightBackground: "#F7F7F8"
    readonly property color lightSurface: "#FFFFFF"
    readonly property color lightSurfaceAlt: "#EFEFF1"
    readonly property color lightText: "#1A1A1A"
    readonly property color lightTextMuted: "#6B6B6B"
    readonly property color lightBorder: "#DDDDDD"

    readonly property color accent: "#FFD700"
    readonly property color danger: "#E74C3C"
    readonly property color success: "#2ECC71"

    property color background: darkMode ? darkBackground : lightBackground
    property color surface: darkMode ? darkSurface : lightSurface
    property color surfaceAlt: darkMode ? darkSurfaceAlt : lightSurfaceAlt
    property color textColor: darkMode ? darkText : lightText
    property color textMuted: darkMode ? darkTextMuted : lightTextMuted
    property color border: darkMode ? darkBorder : lightBorder

    readonly property int radiusSmall: 6
    readonly property int radiusMedium: 10
    readonly property int spacingSmall: 8
    readonly property int spacingMedium: 16
    readonly property int spacingLarge: 24

    readonly property string fontFamily: "Vazirmatn"
}
