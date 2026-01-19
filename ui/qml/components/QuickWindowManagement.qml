// D:\Projects\PycharmProjects\QuickLauncher\ui\qml\components\QuickWindowManagement.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: quickWindowManagement
    anchors.fill: parent

    property var config: ({})
    property var apps: []
    property var appOrder: []


    // 重置确认对话框
    Dialog {
        id: resetDialog
        title: "重置配置"
        modal: true
        standardButtons: Dialog.Yes | Dialog.No

        Text {
            text: "确定要重置所有配置为默认值吗？"
            color: "#000"
        }

        onAccepted: {
            resetToDefaults()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        // 配置设置区域
        GroupBox {
            id: settingsGroup
            Layout.fillWidth: true
            Layout.preferredHeight: 300
            title: "快捷窗口设置"
            background: Rectangle {
                color: "#FFFFFF"
                border.color: "#CCCCCC"
                border.width: 1
                radius: 8
            }

            label: Label {
                text: "快捷窗口设置"
                color: "#000"
                font.pixelSize: 14
                font.bold: true
                leftPadding: 10
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 15

                // 第一行：基本设置
                RowLayout {
                    spacing: 20

                    // 显示快捷窗口
                    ColumnLayout {
                        spacing: 5

                        Text {
                            text: "开机启动"
                            color: "#000"
                            font.pixelSize: 12
                        }

                        Rectangle {
                            id: autoStartCheckbox
                            width: 40
                            height: 20
                            radius: 10
                            color: autoStartCheckbox.checked ? "#4CAF50" : "#666"

                            property bool checked: false

                            Rectangle {
                                id: autoStartHandle
                                width: 16
                                height: 16
                                radius: 8
                                color: "white"
                                anchors.verticalCenter: parent.verticalCenter
                                x: autoStartCheckbox.checked ? parent.width - width - 2 : 2

                                Behavior on x {
                                    NumberAnimation {
                                        duration: 200
                                    }
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    autoStartCheckbox.checked = !autoStartCheckbox.checked
                                    mainWindowBackend.update_main_window_config("auto_start", autoStartCheckbox.checked)

                                }
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                    }

                    // 开机启动
                    ColumnLayout {
                        spacing: 5

                        Text {
                            text: "显示快捷窗口"
                            color: "#000"
                            font.pixelSize: 12
                        }

                        Rectangle {
                            id: showOnStartupCheckbox
                            width: 40
                            height: 20
                            radius: 10
                            color: showOnStartupCheckbox.checked ? "#4CAF50" : "#666"

                            property bool checked: false

                            Rectangle {
                                id: showOnStartupHandle
                                width: 16
                                height: 16
                                radius: 8
                                color: "white"
                                anchors.verticalCenter: parent.verticalCenter
                                x: showOnStartupCheckbox.checked ? parent.width - width - 2 : 2

                                Behavior on x {
                                    NumberAnimation {
                                        duration: 200
                                    }
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    showOnStartupCheckbox.checked = !showOnStartupCheckbox.checked
                                    mainWindowBackend.update_quick_window_config("show_on_startup", showOnStartupCheckbox.checked)
                                }
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                    }

                    // 显示应用名称
                    ColumnLayout {
                        spacing: 5

                        Text {
                            text: "显示应用名"
                            color: "#000"
                            font.pixelSize: 12
                        }

                        Rectangle {
                            id: showLabelsCheckbox
                            width: 40
                            height: 20
                            radius: 10
                            color: showLabelsCheckbox.checked ? "#4CAF50" : "#666"

                            property bool checked: false

                            Rectangle {
                                id: showLabelsHandle
                                width: 16
                                height: 16
                                radius: 8
                                color: "white"
                                anchors.verticalCenter: parent.verticalCenter
                                x: showLabelsCheckbox.checked ? parent.width - width - 2 : 2

                                Behavior on x {
                                    NumberAnimation {
                                        duration: 200
                                    }
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    showLabelsCheckbox.checked = !showLabelsCheckbox.checked
                                    mainWindowBackend.update_quick_window_config("show_labels", showLabelsCheckbox.checked)
                                }
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                    }
                }

                // 第二行：外观设置
                ColumnLayout {
                    spacing: 10

                    // 透明度设置
                    RowLayout {
                        spacing: 10

                        Text {
                            text: "透明度:"
                            Layout.minimumWidth: 80
                            color: "#000"
                        }

                        Slider {
                            id: opacitySlider
                            Layout.fillWidth: true
                            from: 0.1
                            to: 1.0
                            value: 0.9
                            stepSize: 0.05

                            background: Rectangle {
                                x: opacitySlider.leftPadding
                                y: opacitySlider.topPadding + opacitySlider.availableHeight / 2 - height / 2
                                implicitWidth: 200
                                implicitHeight: 4
                                width: opacitySlider.availableWidth
                                height: implicitHeight
                                radius: 2
                                color: "#444"

                                Rectangle {
                                    width: opacitySlider.visualPosition * parent.width
                                    height: parent.height
                                    color: "#007ACC"
                                    radius: 2
                                }
                            }

                            handle: Rectangle {
                                x: opacitySlider.leftPadding + opacitySlider.visualPosition * (opacitySlider.availableWidth - width)
                                y: opacitySlider.topPadding + opacitySlider.availableHeight / 2 - height / 2
                                implicitWidth: 16
                                implicitHeight: 16
                                radius: 8
                                color: opacitySlider.pressed ? "#005A9E" : "#007ACC"
                                border.color: "#BDBDBD"
                            }

                            onValueChanged: {
                                // 每次值改变都更新配置，不仅仅是当滑块有焦点时
                                mainWindowBackend.update_quick_window_config("opacity", value)
                            }
                        }

                        Text {
                            text: Math.round(opacitySlider.value * 100) + "%"
                            Layout.minimumWidth: 40
                            color: "#000"
                            font.pixelSize: 12
                        }
                    }

                    // 图标大小设置
                    RowLayout {
                        spacing: 10

                        Text {
                            text: "图标大小:"
                            Layout.minimumWidth: 80
                            color: "#000"
                        }

                        Slider {
                            id: iconSizeSlider
                            Layout.fillWidth: true
                            from: 32
                            to: 128
                            value: 64
                            stepSize: 8

                            background: Rectangle {
                                x: iconSizeSlider.leftPadding
                                y: iconSizeSlider.topPadding + iconSizeSlider.availableHeight / 2 - height / 2
                                implicitWidth: 200
                                implicitHeight: 4
                                width: iconSizeSlider.availableWidth
                                height: implicitHeight
                                radius: 2
                                color: "#444"

                                Rectangle {
                                    width: iconSizeSlider.visualPosition * parent.width
                                    height: parent.height
                                    color: "#4CAF50"
                                    radius: 2
                                }
                            }

                            handle: Rectangle {
                                x: iconSizeSlider.leftPadding + iconSizeSlider.visualPosition * (iconSizeSlider.availableWidth - width)
                                y: iconSizeSlider.topPadding + iconSizeSlider.availableHeight / 2 - height / 2
                                implicitWidth: 16
                                implicitHeight: 16
                                radius: 8
                                color: iconSizeSlider.pressed ? "#388E3C" : "#4CAF50"
                                border.color: "#BDBDBD"
                            }

                            onValueChanged: {
                                if (iconSizeSlider.activeFocus) {
                                    mainWindowBackend.update_quick_window_config("icon_size", value)
                                }
                            }
                        }

                        Text {
                            text: iconSizeSlider.value + "px"
                            Layout.minimumWidth: 40
                            color: "#000"
                            font.pixelSize: 12
                        }
                    }

                    // 悬停放大效果
                    RowLayout {
                        spacing: 10

                        Text {
                            text: "悬停放大:"
                            Layout.minimumWidth: 80
                            color: "#000"
                        }

                        Slider {
                            id: hoverScaleSlider
                            Layout.fillWidth: true
                            from: 1.0
                            to: 2.0
                            value: 1.2
                            stepSize: 0.1

                            background: Rectangle {
                                x: hoverScaleSlider.leftPadding
                                y: hoverScaleSlider.topPadding + hoverScaleSlider.availableHeight / 2 - height / 2
                                implicitWidth: 200
                                implicitHeight: 4
                                width: hoverScaleSlider.availableWidth
                                height: implicitHeight
                                radius: 2
                                color: "#444"

                                Rectangle {
                                    width: hoverScaleSlider.visualPosition * parent.width
                                    height: parent.height
                                    color: "#FF9800"
                                    radius: 2
                                }
                            }

                            handle: Rectangle {
                                x: hoverScaleSlider.leftPadding + hoverScaleSlider.visualPosition * (hoverScaleSlider.availableWidth - width)
                                y: hoverScaleSlider.topPadding + hoverScaleSlider.availableHeight / 2 - height / 2
                                implicitWidth: 16
                                implicitHeight: 16
                                radius: 8
                                color: hoverScaleSlider.pressed ? "#F57C00" : "#FF9800"
                                border.color: "#BDBDBD"
                            }

                            onValueChanged: {
                                if (hoverScaleSlider.activeFocus) {
                                    mainWindowBackend.update_quick_window_config("hover_scale", parseFloat(value.toFixed(1)))
                                }
                            }
                        }

                        Text {
                            text: "x" + hoverScaleSlider.value.toFixed(1)
                            Layout.minimumWidth: 40
                            color: "#000"
                            font.pixelSize: 12
                        }
                    }
                }

                // 第三行：位置设置
                RowLayout {
                    spacing: 20

                    // 位置选择
                    ColumnLayout {
                        spacing: 5

                        Text {
                            text: "窗口位置"
                            color: "#000"
                            font.pixelSize: 12
                        }

                        Row {
                            spacing: 10

                            Rectangle {
                                id: topPositionBtn
                                width: 60
                                height: 30
                                radius: 5
                                color: positionSelector.currentIndex === 0 ? "#007ACC" : "#a1a1a1"

                                Text {
                                    anchors.centerIn: parent
                                    text: "顶部"
                                    color: "#000"
                                    font.pixelSize: 12
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        positionSelector.currentIndex = 0

                                        mainWindowBackend.update_quick_window_config("position", "top_center")


                                    }
                                    cursorShape: Qt.PointingHandCursor
                                }
                            }

                            Rectangle {
                                id: bottomPositionBtn
                                width: 60
                                height: 30
                                radius: 5
                                color: positionSelector.currentIndex === 1 ? "#007ACC" : "#a1a1a1"

                                Text {
                                    anchors.centerIn: parent
                                    text: "底部"
                                    color: "#000"
                                    font.pixelSize: 12
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        positionSelector.currentIndex = 1
                                        mainWindowBackend.update_quick_window_config("position", "bottom_center")

                                    }
                                    cursorShape: Qt.PointingHandCursor
                                }
                            }
                        }
                    }

                    // 行列按钮
                    ColumnLayout {
                        spacing: 5

                        Text {
                            text: "窗口行数"
                            color: "#000"
                            font.pixelSize: 12
                        }

                        Row {
                            spacing: 5

                            Rectangle {
                                id: decreaseRowsBtn
                                width: 30
                                height: 30
                                radius: 5
                                color: "#007ACC"

                                Text {
                                    anchors.centerIn: parent
                                    text: "-"
                                    color: "#FFF"
                                    font.pixelSize: 16
                                    font.bold: true
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        decrease_rows()
                                    }
                                    cursorShape: Qt.PointingHandCursor
                                }
                            }

                            Rectangle {
                                id: rowsValueLabel
                                width: 40
                                height: 30
                                radius: 5
                                color: "#E0E0E0"

                                Text {
                                    anchors.centerIn: parent
                                    text: config.rows !== undefined ? config.rows : 1
                                    color: "#000"
                                    font.pixelSize: 12
                                }
                            }

                            Rectangle {
                                id: increaseRowsBtn
                                width: 30
                                height: 30
                                radius: 5
                                color: "#007ACC"

                                Text {
                                    anchors.centerIn: parent
                                    text: "+"
                                    color: "#FFF"
                                    font.pixelSize: 16
                                    font.bold: true
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        increase_rows()

                                    }
                                    cursorShape: Qt.PointingHandCursor
                                }
                            }
                        }
                    }

                    ColumnLayout {
                        spacing: 5

                        Text {
                            text: "窗口列数"
                            color: "#000"
                            font.pixelSize: 12
                        }

                        Row {
                            spacing: 5

                            Rectangle {
                                id: decreaseColsBtn
                                width: 30
                                height: 30
                                radius: 5
                                color: "#007ACC"

                                Text {
                                    anchors.centerIn: parent
                                    text: "-"
                                    color: "#FFF"
                                    font.pixelSize: 16
                                    font.bold: true
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        decrease_cols()
                                    }
                                    cursorShape: Qt.PointingHandCursor
                                }
                            }

                            Rectangle {
                                id: colsValueLabel
                                width: 40
                                height: 30
                                radius: 5
                                color: "#E0E0E0"

                                Text {
                                    anchors.centerIn: parent
                                    text: config.cols !== undefined ? config.cols : 5
                                    color: "#000"
                                    font.pixelSize: 12
                                }
                            }

                            Rectangle {
                                id: increaseColsBtn
                                width: 30
                                height: 30
                                radius: 5
                                color: "#007ACC"

                                Text {
                                    anchors.centerIn: parent
                                    text: "+"
                                    color: "#FFF"
                                    font.pixelSize: 16
                                    font.bold: true
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        increase_cols()
                                    }
                                    cursorShape: Qt.PointingHandCursor
                                }
                            }
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                    }
                }


            }
        }

        // 应用排序区域
        GroupBox {
            Layout.fillWidth: true
            Layout.fillHeight: true
            title: "应用排序"
            background: Rectangle {
                color: "#FFFFFF"
                border.color: "#CCCCCC"
                border.width: 1
                radius: 5
            }

            label: Label {
                text: "应用排序（拖拽排序）"
                color: "#000"
                font.pixelSize: 14
                font.bold: true
                leftPadding: 10
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                // 工具栏
                RowLayout {
                    spacing: 10

                    Text {
                        text: "所有应用:"
                        color: "#000"
                        font.pixelSize: 12
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    // 重置刷新顺序按钮
                    Rectangle {
                        width: 100
                        height: 30
                        radius: 5
                        color: "#FF9800"

                        Text {
                            anchors.centerIn: parent
                            text: "刷新顺序"
                            color: "white"
                            font.pixelSize: 12
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                resetAppOrder()
                            }
                            cursorShape: Qt.PointingHandCursor
                        }
                    }

                    // 保存顺序按钮
                    Rectangle {
                        width: 100
                        height: 30
                        radius: 5
                        color: "#4CAF50"

                        Text {
                            anchors.centerIn: parent
                            text: "保存顺序"
                            color: "white"
                            font.pixelSize: 12
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                saveAppOrder()
                            }
                            cursorShape: Qt.PointingHandCursor
                        }
                    }
                }

                // 分为两个部分：可用应用和已选应用 - 按8:2比例
                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 10

                    // 可用应用列表 - 20%宽度
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredWidth: parent.width * 0.2

                        // 搜索栏 - 在所有应用文本下方
                        RowLayout {
                            spacing: 10
                            Layout.fillWidth: true

                            TextField {
                                id: searchField
                                Layout.fillWidth: true
                                placeholderText: "搜索应用..."
                                color: "#000"
                                selectByMouse: true
                                background: Rectangle {
                                    color: "#F0F0F0"
                                }
                                onTextChanged: {
                                    filterApps()
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#FFFFFF"
                            border.color: "#CCCCCC"
                            border.width: 1
                            radius: 3

                            GridView {  // 改为GridView以实现网格布局
                                id: allAppsListView
                                anchors.fill: parent
                                anchors.margins: 5
                                clip: true
                                cellWidth: 60 // 每个图标单元格宽度
                                cellHeight: 60  // 每个图标单元格高度
                                model: ListModel {
                                    id: allAppsModel
                                }

                                // 启用拖拽（虽然主要用于右侧，但为了保持一致性设置）
                                interactive: true

                                delegate: Rectangle {
                                    width: 60  // 固定宽度，与图标大小一致
                                    height: 60 // 固定高度，与图标大小一致
                                    color: index % 2 ? "#F0F0F0" : "#E0E0E0"
                                    radius: 3

                                    Row {
                                        anchors.centerIn: parent
                                        spacing: 0

                                        // 应用图标
                                        Image {
                                            id: allAppIcon
                                            width: 48
                                            height: 48
                                            source: model.icon_path ? model.icon_path : ("image://icon/" + encodeURIComponent(model.path))
                                            fillMode: Image.PreserveAspectFit
                                            sourceSize.width: 48
                                            sourceSize.height: 48
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                    }

                                    // 添加按钮覆盖整个图标区域
                                    Rectangle {
                                        anchors.centerIn: parent
                                        width: 25
                                        height: 25
                                        radius: 12.5
                                        color: "#4CAF50"
                                        border.color: "white"
                                        border.width: 2

                                        Text {
                                            anchors.centerIn: parent
                                            text: "+"
                                            color: "#000"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                // 检查是否已经存在于快捷应用列表中
                                                var exists = false
                                                for (var i = 0; i < quickAppsModel.count; i++) {
                                                    if (quickAppsModel.get(i).id === model.id) {
                                                        exists = true
                                                        break
                                                    }
                                                }

                                                if (!exists) {
                                                    // 添加到已选应用列表
                                                    quickAppsModel.append({
                                                        "id": model.id,
                                                        "name": model.name,
                                                        "path": model.path,
                                                        "icon_path": model.icon_path
                                                    })
                                                    // 从所有应用列表移除
                                                    allAppsModel.remove(index, 1)
                                                    // 更新配置
                                                    updateAppOrder()

                                                    // 重新应用搜索过滤
                                                    filterApps()

                                                    // 显示成功消息
                                                    mainWindowBackend.showMessage("成功", "应用已添加到快捷窗口", "success")
                                                } else {
                                                    // 显示重复添加的警告
                                                    mainWindowBackend.showMessage("警告", "应用已在快捷窗口中，不能重复添加", "warning")
                                                }
                                            }
                                            cursorShape: Qt.PointingHandCursor
                                        }
                                    }
                                }

                                // 如果没有应用
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 300
                                    height: 100
                                    color: "transparent"
                                    visible: allAppsModel.count === 0

                                    Column {
                                        anchors.centerIn: parent
                                        spacing: 10

                                        Text {
                                            text: ""
                                            color: "#666"
                                            font.pixelSize: 32
                                            anchors.horizontalCenter: parent.horizontalCenter
                                        }

                                        Text {
                                            text: "暂无应用"
                                            color: "#666"
                                            font.pixelSize: 14
                                            anchors.horizontalCenter: parent.horizontalCenter
                                        }

                                        Text {
                                            text: "请先添加应用"
                                            color: "#000"
                                            font.pixelSize: 12
                                            anchors.horizontalCenter: parent.horizontalCenter
                                        }
                                    }
                                }

                                ScrollBar.vertical: ScrollBar {
                                    id: allAppsScrollbar
                                    policy: ScrollBar.AlwaysOn
                                    width: 12

                                    background: Rectangle {
                                        color: "transparent"  // 透明背景以避免黑色背景问题

                                        Rectangle {
                                            width: parent.width
                                            height: parent.height
                                            color: "#f0f0f0"

                                            Rectangle {
                                                anchors.centerIn: parent
                                                width: 6
                                                height: parent.height
                                                color: "#c0c0c0"
                                                visible: allAppsScrollbar.size < 1.0
                                            }
                                        }
                                    }

                                    contentItem: Rectangle {
                                        implicitWidth: 12
                                        implicitHeight: 30
                                        radius: 6
                                        color: "#a0a0a0"

                                        states: State {
                                            when: allAppsScrollbar.pressed
                                            PropertyChanges {
                                                target: allAppsScrollbar.contentItem
                                                color: "#808080"
                                            }
                                        }

                                        transitions: Transition {
                                            from: "*";
                                            to: "pressed"
                                            NumberAnimation {
                                                properties: "color";
                                                duration: 100
                                                easing.type: Easing.InOutCubic
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // 已选应用列表
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredWidth: parent.width * 0.8

                        Text {
                            text: "快捷应用:"
                            color: "#000"
                            font.pixelSize: 12
                            Layout.leftMargin: 5
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#FFFFFF"
                            border.color: "#CCCCCC"
                            border.width: 1
                            radius: 3

                            // 水平滚动容器，用于横向排列已选应用
                            ScrollView {
                                anchors.fill: parent
                                anchors.margins: 5


                                ListView {
                                    id: quickAppsListView
                                    orientation: ListView.Horizontal
                                    spacing: 10
                                    height: parent.height
                                    model: ListModel {
                                        id: quickAppsModel
                                    }

                                    // 启用拖拽功能
                                    interactive: true

                                    delegate: Rectangle {
                                        width: 48 // 固定宽度，与图标大小一致
                                        height: 80 - quickAppsScrollbar.height
                                        color: "#F0F0F0"
                                        border.color: "#CCCCCC"
                                        border.width: 1
                                        radius: 3

                                        property int visualIndex: index

                                        // 拖拽处理
                                        Drag.active: dragArea.drag.active
                                        Drag.hotSpot.x: width / 2
                                        Drag.hotSpot.y: height / 2

                                        Column {
                                            anchors.centerIn: parent
                                            spacing: 5

                                            // 应用图标
                                            Image {
                                                id: appIcon
                                                width: 48
                                                height: 48
                                                source: model.icon_path ? model.icon_path : ("image://icon/" + encodeURIComponent(model.path))
                                                fillMode: Image.PreserveAspectFit
                                                sourceSize.width: 48
                                                sourceSize.height: 48
                                                anchors.horizontalCenter: parent.horizontalCenter
                                            }

                                            // 移除按钮
                                            Rectangle {
                                                width: 12
                                                height: 12
                                                radius: 10
                                                color: "#F44336"
                                                anchors.horizontalCenter: parent.horizontalCenter

                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "×"
                                                    color: "#000"
                                                    font.pixelSize: 12
                                                    font.bold: true
                                                }

                                                MouseArea {
                                                    anchors.fill: parent
                                                    onClicked: {
                                                        // 添加回原始所有应用列表
                                                        var existsInOriginal = false
                                                        for (var i = 0; i < originalAllApps.length; i++) {
                                                            if (originalAllApps[i].id === model.id) {
                                                                existsInOriginal = true
                                                                break
                                                            }
                                                        }

                                                        if (!existsInOriginal) {
                                                            originalAllApps.push({
                                                                "id": model.id,
                                                                "name": model.name,
                                                                "path": model.path,
                                                                "icon_path": model.icon_path
                                                            })
                                                        }

                                                        // 从已选应用列表移除
                                                        quickAppsModel.remove(index, 1)
                                                        // 更新配置
                                                        updateAppOrder()

                                                        // 重新应用搜索过滤
                                                        filterApps()
                                                    }
                                                    cursorShape: Qt.PointingHandCursor
                                                }
                                            }
                                        }

                                        // 拖拽区域 - 仅在图标区域响应拖拽，避免与移除按钮冲突
                                        MouseArea {
                                            id: dragArea
                                            x: (parent.width - 50) / 2
                                            y: 10
                                            width: 50
                                            height: 50
                                            drag.target: parent
                                            drag.axis: Drag.XAxis
                                            propagateComposedEvents: true

                                            onPressed: {
                                                parent.z = 100
                                                parent.opacity = 0.8
                                            }

                                            onReleased: {
                                                parent.Drag.drop()
                                                parent.z = 0
                                                parent.opacity = 1.0
                                                // 拖拽后更新配置
                                                updateAppOrder()

                                                // 重新应用搜索过滤
                                                filterApps()
                                            }

                                            // 阻止点击事件传播，避免拖拽后误触其他功能
                                            onClicked: {
                                                mouse.accepted = true
                                            }
                                        }

                                        // 放置区域
                                        DropArea {
                                            anchors.fill: parent
                                            onEntered: {
                                                if (drag.source && drag.source.visualIndex !== parent.visualIndex) {
                                                    quickAppsModel.move(drag.source.visualIndex, parent.visualIndex, 1)
                                                    drag.source.visualIndex = parent.visualIndex
                                                    updateAppOrder() // 拖拽后立即更新配置
                                                }
                                            }
                                            onDropped: {
                                                // 拖拽放置后重新应用搜索过滤
                                                filterApps()
                                            }
                                        }
                                    }

                                    // 如果没有已选应用
                                    Rectangle {
                                        anchors.centerIn: parent
                                        width: 300
                                        height: 100
                                        color: "transparent"
                                        visible: quickAppsModel.count === 0

                                        Column {
                                            anchors.centerIn: parent
                                            spacing: 10

                                            Text {
                                                text: ""
                                                color: "#666"
                                                font.pixelSize: 32
                                                anchors.horizontalCenter: parent.horizontalCenter
                                            }

                                            Text {
                                                text: "暂无已选应用"
                                                color: "#666"
                                                font.pixelSize: 14
                                                anchors.horizontalCenter: parent.horizontalCenter
                                            }

                                            Text {
                                                text: "请从左侧添加应用"
                                                color: "#000"
                                                font.pixelSize: 12
                                                anchors.horizontalCenter: parent.horizontalCenter
                                            }
                                        }
                                    }
                                }

                                ScrollBar.horizontal: ScrollBar {
                                    id: quickAppsScrollbar
                                    policy: ScrollBar.AsNeeded
                                    height: 12  // 调整滚动条高度
                                    width: 400

                                    background: Rectangle {
                                        anchors.fill: parent
                                        color: "transparent"  // 透明背景以避免黑色背景问题

                                        Rectangle {
                                            anchors.fill: parent
                                            anchors.margins: 0
                                            color: "#f0f0f0"

                                            Rectangle {
                                                anchors.centerIn: parent
                                                anchors.margins: 0
                                                width: parent.width
                                                height: 6
                                                color: "#c0c0c0"
                                                visible: quickAppsScrollbar.size < 1.0
                                            }
                                        }
                                    }

                                    contentItem: Rectangle {
                                        implicitWidth: 30
                                        implicitHeight: 12  // 调整内容项高度以匹配滚动条高度
                                        radius: 6
                                        color: "#a0a0a0"

                                        states: State {
                                            when: quickAppsScrollbar.pressed
                                            PropertyChanges {

                                                target: quickAppsScrollbar.contentItem
                                                color: "#808080"
                                            }
                                        }

                                        transitions: Transition {
                                            from: "*";
                                            to: "pressed"
                                            NumberAnimation {
                                                properties: "color";
                                                duration: 100
                                                easing.type: Easing.InOutCubic
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // 底部操作栏
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Item {
                Layout.fillWidth: true
            }


            // 重置配置按钮
            Rectangle {
                width: 120
                height: 40
                radius: 5
                color: "#F44336"

                Text {
                    anchors.centerIn: parent
                    text: "重置配置"
                    color: "#000"
                    font.pixelSize: 14
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        resetDialog.open()
                    }
                    cursorShape: Qt.PointingHandCursor
                }
            }

            // 刷新快捷窗口布局按钮
            Rectangle {
                width: 140
                height: 40
                radius: 5
                color: "#FF9800"

                Text {
                    anchors.centerIn: parent
                    text: "刷新窗口布局"
                    color: "#000"
                    font.pixelSize: 14
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        quickWindowBackend.refresh_with_single_row()
                        mainWindowBackend.showMessage("提示", "快捷窗口布局已刷新", "info")
                    }
                    cursorShape: Qt.PointingHandCursor
                }
            }

            // 保存配置按钮
            Rectangle {
                width: 120
                height: 40
                radius: 5
                color: "#4CAF50"

                Text {
                    anchors.centerIn: parent
                    text: "保存配置"
                    color: "#000"
                    font.pixelSize: 14
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        saveAllConfig()
                    }
                    cursorShape: Qt.PointingHandCursor
                }
            }
        }
    }

    // 属性
    property QtObject positionSelector: QtObject
    {
        property int currentIndex: 1
    }

    // 存储原始应用数据
    property var originalAllApps: []

    // 更新应用顺序
    function updateAppOrder() {
        var order = []
        var seenIds = {} // 用于检查重复ID
        for (var i = 0; i < quickAppsModel.count; i++) {
            var appId = quickAppsModel.get(i).id
            if (!seenIds[appId]) { // 避免重复添加相同的ID
                order.push(appId)
                seenIds[appId] = true
            }
        }

        // 使用manage_quick_window_apps方法更新应用顺序
        mainWindowBackend.manage_quick_window_apps("reorder", order)
    }

    // 过滤应用
    function filterApps() {
        // 清空当前显示的列表
        allAppsModel.clear()

        // 获取快捷窗口中已有的应用ID
        var quickAppIds = {}
        for (var j = 0; j < quickAppsModel.count; j++) {
            var quickApp = quickAppsModel.get(j)
            quickAppIds[quickApp.id] = true
        }

        // 根据搜索框内容过滤应用
        var searchText = searchField.text.toLowerCase()
        for (var i = 0; i < originalAllApps.length; i++) {
            var app = originalAllApps[i]

            // 检查应用名称是否匹配搜索词，且未在快捷窗口中
            if (app.name.toLowerCase().includes(searchText) &&
                !quickAppIds[app.id]) {
                allAppsModel.append(app)
            }
        }
    }

    // 初始化配置
    Component.onCompleted: {
        console.log("QuickWindowManagement组件加载完成")

        // 加载配置
        loadConfig()

        // 加载应用列表
        loadApps()
    }

    // 加载配置
    function loadConfig() {
        config = mainWindowBackend.get_quick_window_config()
        console.log("加载配置:", JSON.stringify(config))

        // 设置控件值
        if (config.opacity !== undefined) {
            opacitySlider.value = config.opacity
        }
        if (config.icon_size !== undefined) {
            iconSizeSlider.value = config.icon_size
        }
        if (config.hover_scale !== undefined) {
            hoverScaleSlider.value = config.hover_scale
        }
        if (config.auto_start !== undefined) {
            autoStartCheckbox.checked = config.auto_start
        }
        if (config.show_on_startup !== undefined) {
            showOnStartupCheckbox.checked = config.show_on_startup
        }
        if (config.show_labels !== undefined) {
            showLabelsCheckbox.checked = config.show_labels
        }
        if (config.position !== undefined) {
            positionSelector.currentIndex = config.position === "top_center" ? 0 : 1
        }

        // 加载应用顺序
        if (config.app_order !== undefined) {
            appOrder = config.app_order
        }
    }

    // 加载应用列表
    function loadApps() {
        apps = mainWindowBackend.get_applications()
        console.log("加载应用数量:", apps.length)

        // 按配置中的顺序排列应用
        var orderedApps = []
        var remainingApps = []

        // 首先按配置中的顺序添加应用到已选列表
        if (appOrder && appOrder.length > 0) {
            for (var i = 0; i < appOrder.length; i++) {
                for (var j = 0; j < apps.length; j++) {
                    if (apps[j].id === appOrder[i]) {
                        orderedApps.push(apps[j])
                        break
                    }
                }
            }
        }

        // 将剩余的应用添加到未选列表
        for (var k = 0; k < apps.length; k++) {
            var exists = false
            for (var l = 0; l < orderedApps.length; l++) {
                if (orderedApps[l].id === apps[k].id) {
                    exists = true
                    break
                }
            }
            if (!exists) {
                remainingApps.push(apps[k])
            }
        }

        // 更新已选应用模型
        quickAppsModel.clear()
        for (var m = 0; m < orderedApps.length; m++) {
            quickAppsModel.append(orderedApps[m])
        }

        // 更新所有应用模型
        allAppsModel.clear()
        originalAllApps = [] // 重置原始数据
        for (var n = 0; n < remainingApps.length; n++) {
            allAppsModel.append(remainingApps[n])
            originalAllApps.push(remainingApps[n]) // 保存原始数据用于搜索
        }

        // 确保应用顺序配置与当前状态一致
        updateAppOrder()

        // 重新应用搜索过滤
        filterApps()
    }

    // 保存应用顺序
    function saveAppOrder() {
        var order = []
        var seenIds = {} // 用于检查重复ID
        for (var i = 0; i < quickAppsModel.count; i++) {
            var appId = quickAppsModel.get(i).id
            if (!seenIds[appId]) { // 避免重复添加相同的ID
                order.push(appId)
                seenIds[appId] = true
            }
        }

        mainWindowBackend.update_quick_window_config("app_order", order)
        mainWindowBackend.showMessage("成功", "应用顺序已保存", "success")
    }

    // 重置应用顺序
    function resetAppOrder() {
        // 将所有已选应用移到未选列表
        while (quickAppsModel.count > 0) {
            allAppsModel.append(quickAppsModel.get(0))
            originalAllApps.push(quickAppsModel.get(0))
            quickAppsModel.remove(0)
        }

        // 重新加载所有应用（因为重置后应该显示所有应用）
        loadApps()

        // 更新配置 - 重置后应用顺序应为空
        updateAppOrder()

        mainWindowBackend.showMessage("提示", "应用顺序已重置", "info")
    }

    // 预览快捷窗口
    function previewQuickWindow() {
        // 这里可以添加预览逻辑
        mainWindowBackend.showMessage("预览", "快捷窗口预览功能正在开发中", "info")
    }

    // 保存所有配置
    function saveAllConfig() {
        // 保存当前配置
        mainWindowBackend.update_quick_window_config("opacity", parseFloat(opacitySlider.value))
        mainWindowBackend.update_quick_window_config("icon_size", parseInt(iconSizeSlider.value))
        mainWindowBackend.update_quick_window_config("hover_scale", parseFloat(hoverScaleSlider.value.toFixed(1)))
        mainWindowBackend.update_quick_window_config("max_icons_per_row", 10)
        mainWindowBackend.update_quick_window_config("auto_start", Boolean(autoStartCheckbox.checked))
        mainWindowBackend.update_quick_window_config("show_on_startup", Boolean(showOnStartupCheckbox.checked))
        mainWindowBackend.update_quick_window_config("show_labels", Boolean(showLabelsCheckbox.checked))
        mainWindowBackend.update_quick_window_config("position", positionSelector.currentIndex === 0 ? "top_center" : "bottom_center")
        mainWindowBackend.update_quick_window_config("opacity_noise", parseFloat(opacityNoiseSlider.value))
        mainWindowBackend.update_quick_window_config("opacity_tint", parseFloat(opacityTintSlider.value))
        mainWindowBackend.update_quick_window_config("radius_blur", parseInt(radiusBlurSlider.value))

        // 保存应用顺序
        saveAppOrder()

        mainWindowBackend.showMessage("成功", "所有配置已保存", "success")
    }

    // 重置为默认值
    function resetToDefaults() {
        // 重置所有控件为默认值
        opacitySlider.value = 0.25
        iconSizeSlider.value = 48
        hoverScaleSlider.value = 1.5
        autoStartCheckbox.checked = false
        showOnStartupCheckbox.checked = true
        showLabelsCheckbox.checked = false
        positionSelector.currentIndex = 1
        opacityNoiseSlider.value = 0.01
        opacityTintSlider.value = 0.15
        radiusBlurSlider.value = 20

        // 重置配置
        var defaultConfig = {
            auto_start: false,
            show_on_startup:true,
            show_labels: false,
            position: "bottom_center",
            size: 64,
            opacity: 0.25,
            hover_scale: 1.5,
            app_order: [],
            max_icons_per_row: 10,
            icon_size: 64,
            use_system_icons: true,
            opacity_noise: 0.01,
            opacity_tint: 0.15,
            radius_blur: 20
        }

        // 应用默认配置
        for (var key in defaultConfig) {
            mainWindowBackend.update_quick_window_config(key, defaultConfig[key])
        }

        // 重置应用顺序
        resetAppOrder()

        mainWindowBackend.showMessage("成功", "配置已重置为默认值", "success")
    }

    // 连接后端信号
    Connections {
        target: mainWindowBackend

        function onConfigUpdated(newConfig) {
            console.log("收到配置更新信号")
            config = newConfig
            loadConfig()

            // 重新加载应用列表以确保配置更新生效
            loadApps()
        }

        function onAppListUpdated(appsList) {
            console.log("收到应用列表更新信号")
            apps = appsList
            loadApps()
        }
    }

    // 连接快捷窗口后端信号，用于实时更新行列显示
    Connections {
        target: quickWindowBackend

        function onConfigUpdated(newConfig) {
            console.log("收到快捷窗口配置更新信号")
            config = newConfig

            // 更新界面显示的行列值
            updateRowsColsDisplay()
        }
    }

    // 更新行列显示的函数
    function updateRowsColsDisplay() {
        // 更新行数显示
        var currentRows = config.rows !== undefined ? config.rows : 1;
        if (rowsValueLabel.children.length > 0) {
            rowsValueLabel.children[0].text = currentRows;
        }

        // 更新列数显示
        var currentCols = config.cols !== undefined ? config.cols : 5;
        if (colsValueLabel.children.length > 0) {
            colsValueLabel.children[0].text = currentCols;
        }

    }

    function rows_cols() {
        if (config.app_order.length % config.cols === 0) {


        }
    }

    function decrease_rows() {
        var currentRows = config.rows !== undefined ? config.rows : 1;
        if (currentRows > 1) {
            var newRows = currentRows - 1;
            // 立即更新本地配置以提供即时反馈
            config.rows = newRows;
            // 刷新界面以应用新的行数设置
            // quickWindowBackend.refresh_apps();
            // 然后更新后端配置
            mainWindowBackend.update_quick_window_config("rows", newRows);
            // 更新显示
            updateRowsColsDisplay();
        }

    }

    function increase_rows() {
        var currentRows = config.rows !== undefined ? config.rows : 1;
        if (currentRows < Math.min(config.app_order.length / config.cols, 15)) {
            var newRows = currentRows + 1;
            // 立即更新本地配置以提供即时反馈
            config.rows = newRows;
            // 刷新界面以应用新的行数设置
            // quickWindowBackend.refresh_apps();
            // 然后更新后端配置
            mainWindowBackend.update_quick_window_config("rows", newRows);
            // 更新显示
            updateRowsColsDisplay();
        }
    }

    function decrease_cols() {
        var currentCols = config.cols !== undefined ? config.cols : 5;
        if (currentCols > 1) {
            var newCols = currentCols - 1;
            // 立即更新本地配置以提供即时反馈
            config.cols = newCols;
            quickWindowBackend.refresh_with_single_row();
            // 然后更新后端配置
            mainWindowBackend.update_quick_window_config("cols", newCols);
            // 更新显示
            updateRowsColsDisplay();
        }
    }

    function increase_cols() {
        var currentCols = config.cols !== undefined ? config.cols : 5;
        if (currentCols < Math.min(config.app_order.length, 15)) {
            // 判断加列后减行行数
            var derow = config.rows - Math.ceil(config.app_order.length / (config.cols + 1))
            // // 判断行数
            // var qrow = config.app_order.length % config.cols
            // // 判断加列行数
            // var hrow = config.app_order.length % (config.cols + 1)
            if (config.app_order.length <= config.rows * config.cols) {
                if (derow > 0) {
                    for (var i = 0; i < derow; i++) {
                        decrease_rows()
                    }
                }
            }
            var newCols = currentCols + 1;
            // 立即更新本地配置以提供即时反馈
            config.cols = newCols;
            quickWindowBackend.refresh_with_single_row();
            // 更新显示
            // 然后更新后端配置
            mainWindowBackend.update_quick_window_config("cols", newCols);
            updateRowsColsDisplay();
        }
    }
}
