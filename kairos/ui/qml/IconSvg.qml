import QtQuick
import QtQuick.Shapes

// Ícone line-art a partir de path data SVG (viewBox 24×24 do protótipo).
// Escala para width/height; cor/espessura vêm de fora (tokens do Theme),
// nada hardcoded aqui. Suporta traço (default) ou preenchido (filled).
Item {
    id: root

    property string d: ""                 // path data SVG ('M...'); aceita múltiplos subpaths
    property color stroke: "#000000"
    property real strokeWidth: 2
    property bool filled: false           // ícones sólidos (ex.: play) usam fill, sem traço

    Shape {
        anchors.centerIn: parent
        width: 24
        height: 24
        scale: Math.min(root.width, root.height) / 24
        antialiasing: true

        ShapePath {
            strokeColor: root.filled ? "transparent" : root.stroke
            strokeWidth: root.strokeWidth
            fillColor: root.filled ? root.stroke : "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: root.d }
        }
    }
}
