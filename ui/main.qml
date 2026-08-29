import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import AppBackend 1.0
import "." as Ui

ApplicationWindow {
    id: window
    width: 1280
    height: 800
    minimumWidth: 1000
    minimumHeight: 640
    visible: true
    title: "ابزار برندسازی تصاویر"

    Backend {
        id: backend
    }

    FolderDialog {
        id: inputDirDialog
        title: "انتخاب پوشه تصاویر ورودی"
        onAccepted: backend.setInputDir(selectedFolder)
    }

    FolderDialog {
        id: outputDirDialog
        title: "انتخاب پوشه خروجی"
        onAccepted: backend.setOutputDir(selectedFolder)
    }

    FileDialog {
        id: logoFilesDialog
        title: "انتخاب فایل‌های لوگو"
        fileMode: FileDialog.OpenFiles
        nameFilters: ["تصاویر (*.png *.jpg *.jpeg)"]
        onAccepted: backend.setLogoFiles(selectedFiles)
    }



    LayoutMirroring.enabled: true
    LayoutMirroring.childrenInherit: true

    color: Ui.Theme.background

    font.family: Ui.Theme.fontFamily

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Main preview area
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Ui.Theme.background

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Ui.Theme.spacingLarge
                spacing: Ui.Theme.spacingMedium

                RowLayout {
                    Layout.fillWidth: true

                    Label {
                        text: "پیش‌نمایش"
                        font.pixelSize: 20
                        font.bold: true
                        color: Ui.Theme.textColor
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        text: Ui.Theme.darkMode ? "☀ حالت روشن" : "🌙 حالت تیره"
                        onClicked: Ui.Theme.darkMode = !Ui.Theme.darkMode
                        background: Rectangle {
                            color: Ui.Theme.surfaceAlt
                            radius: Ui.Theme.radiusSmall
                        }
                        contentItem: Text {
                            text: parent.text
                            color: Ui.Theme.textColor
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Ui.Theme.surface
                    radius: Ui.Theme.radiusMedium
                    border.color: Ui.Theme.border
                    border.width: 1
                    clip: true

                    Image {
                        anchors.fill: parent
                        anchors.margins: 12
                        fillMode: Image.PreserveAspectFit
                        source: backend.previewImagePath
                        cache: false
                        visible: backend.previewImagePath.length > 0
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: backend.previewImagePath.length === 0
                        text: "پوشه تصاویر ورودی را انتخاب کنید"
                        color: Ui.Theme.textMuted
                        font.pixelSize: 16
                    }
                }
            }
        }

        // Settings sidebar
        Rectangle {
            Layout.preferredWidth: 360
            Layout.fillHeight: true
            color: Ui.Theme.surface
            border.color: Ui.Theme.border
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Ui.Theme.spacingMedium
                spacing: Ui.Theme.spacingMedium

                Label {
                    text: "تنظیمات"
                    font.pixelSize: 18
                    font.bold: true
                    color: Ui.Theme.textColor
                }

                Label {
                    text: "کنترل‌های گرادیان، لوگو، متن و کادر در نسخه بعد اضافه می‌شوند."
                    color: Ui.Theme.textMuted
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Ui.PickerRow {
                    label: "پوشه تصاویر ورودی"
                    value: backend.inputDir
                    placeholder: "انتخاب نشده"
                    onClicked: inputDirDialog.open()
                }

                Ui.PickerRow {
                    label: "پوشه خروجی"
                    value: backend.outputDir
                    placeholder: "انتخاب نشده"
                    onClicked: outputDirDialog.open()
                }

                Ui.PickerRow {
                    label: "لوگوها"
                    value: backend.logoFiles.length > 0
                           ? backend.logoFiles.length + " فایل انتخاب شد"
                           : ""
                    placeholder: "انتخاب نشده"
                    onClicked: logoFilesDialog.open()
                }

                Label {
                    visible: backend.statusMessage.length > 0
                    text: backend.statusMessage
                    color: Ui.Theme.danger
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    ColumnLayout {
                        width: parent.width
                        spacing: Ui.Theme.spacingMedium

                        Label {
                            text: "گرادیان"
                            color: Ui.Theme.textColor
                            font.bold: true
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Label { text: "فعال"; color: Ui.Theme.textMuted }
                            Item { Layout.fillWidth: true }
                            Switch {
                                checked: backend.gradientEnabled
                                onToggled: backend.gradientEnabled = checked
                            }
                        }

                        Label { text: "ارتفاع گرادیان"; color: Ui.Theme.textMuted }
                        Slider {
                            Layout.fillWidth: true
                            from: 0.1; to: 0.8
                            value: backend.gradientHeight
                            onMoved: backend.gradientHeight = value
                        }

                        Label { text: "شدت گرادیان"; color: Ui.Theme.textMuted }
                        Slider {
                            Layout.fillWidth: true
                            from: 0.0; to: 1.0
                            value: backend.gradientIntensity
                            onMoved: backend.gradientIntensity = value
                        }

                        Label {
                            text: "متن"
                            color: Ui.Theme.textColor
                            font.bold: true
                        }

                        TextField {
                            Layout.fillWidth: true
                            placeholderText: "متن روی تصویر"
                            text: backend.textContent
                            onTextChanged: backend.textContent = text
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            RadioButton {
                                autoExclusive: false
                                text: "بالا وسط"
                                checked: backend.textPosition === "top"
                                onToggled: if (checked) backend.textPosition = "top"
                            }
                            RadioButton {
                                autoExclusive: false
                                text: "پایین وسط"
                                checked: backend.textPosition === "bottom"
                                onToggled: if (checked) backend.textPosition = "bottom"
                            }
                        }

                        Label {
                            text: "کادر تصویر"
                            color: Ui.Theme.textColor
                            font.bold: true
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            RadioButton {
                                autoExclusive: false
                                text: "بدون کادر"
                                checked: backend.borderPreset === "none"
                                onToggled: if (checked) backend.borderPreset = "none"
                            }
                            RadioButton {
                                autoExclusive: false
                                text: "خط نازک ساده"
                                checked: backend.borderPreset === "thin_line"
                                onToggled: if (checked) backend.borderPreset = "thin_line"
                            }
                            RadioButton {
                                autoExclusive: false
                                text: "محو در گوشه‌ها"
                                checked: backend.borderPreset === "fade_corners"
                                onToggled: if (checked) backend.borderPreset = "fade_corners"
                            }
                            RadioButton {
                                autoExclusive: false
                                text: "خط با فاصله دور متن"
                                checked: backend.borderPreset === "fade_text_gap"
                                onToggled: if (checked) backend.borderPreset = "fade_text_gap"
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                Button {
                    Layout.fillWidth: true
                    text: "شروع پردازش"
                    background: Rectangle {
                        color: Ui.Theme.accent
                        radius: Ui.Theme.radiusSmall
                    }
                    contentItem: Text {
                        text: parent.text
                        color: "#1A1A1A"
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }
}
