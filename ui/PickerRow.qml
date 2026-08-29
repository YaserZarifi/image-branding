import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 4

    property string label: ""
    property string value: ""
    property string placeholder: "انتخاب نشده"
    signal clicked()

    Label {
        text: root.label
        color: Theme.textMuted
        font.pixelSize: 13
    }

    Rectangle {
        Layout.fillWidth: true
        height: 44
        radius: Theme.radiusSmall
        color: Theme.surfaceAlt
        border.color: Theme.border
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            Label {
                Layout.fillWidth: true
                text: root.value.length > 0 ? root.value : root.placeholder
                color: root.value.length > 0 ? Theme.textColor : Theme.textMuted
                elide: Text.ElideMiddle
            }

            Label {
                text: "انتخاب"
                color: Theme.accent
                font.bold: true
            }
        }

        MouseArea {
            anchors.fill: parent
            onClicked: root.clicked()
        }
    }
}
