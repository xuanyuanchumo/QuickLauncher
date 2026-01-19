// #file:D:\Projects\PycharmProjects\QuickLauncher\ui\qml\components\AppManagement.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: appManagementRoot
    anchors.fill: parent

    // 应用信息编辑对话框
    Dialog {
        id: editDialog
        title: "编辑应用信息"
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        
        width: 400
        height: 300
        anchors.centerIn: Overlay.overlay

        background: Rectangle {
            color: "#FFFFFF"
            radius: 8
            border.color: "#CCCCCC"
            border.width: 1
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10

            Text {
                text: "应用名称:"
                color: "#000"
                font.pixelSize: 14
            }

            TextField {
                id: editNameField
                Layout.fillWidth: true
                placeholderText: "输入应用名称"
                color: "#000"
                background: Rectangle {
                    color: "#F0F0F0"
                    radius: 3
                }
            }

            Text {
                text: "描述:"
                color: "#000"
                font.pixelSize: 14
            }

            TextArea {
                id: editDescField
                Layout.fillWidth: true
                Layout.fillHeight: true
                placeholderText: "输入应用描述（可选）"
                color: "#000"
                wrapMode: Text.Wrap
                background: Rectangle {
                    color: "#F0F0F0"
                    radius: 3
                }
            }
        }

        onAccepted: {
            if (editNameField.text.trim() !== "") {
                var appId = appListView.currentAppId
                if (appId) {
                    mainWindowBackend.update_application_info(
                        appId,
                        editNameField.text.trim(),
                        editDescField.text.trim()
                    )
                }
            }
        }

        onRejected: {
            editNameField.text = ""
            editDescField.text = ""
        }
    }

    // 确认删除对话框
    Dialog {
        id: confirmDialog
        title: "确认删除"
        modal: true
        standardButtons: Dialog.Yes | Dialog.No
        anchors.centerIn: Overlay.overlay

        background: Rectangle {
            color: "#FFFFFF"
            radius: 8
            border.color: "#CCCCCC"
            border.width: 1
        }

        Text {
            text: "确定要删除选中的应用吗？此操作不可撤销。"
            color: "#000"
        }

        onAccepted: {
            deleteSelectedApps()
        }
    }

    // 导出对话框
    FileDialog {
        id: exportDialog
        title: "导出应用列表"
        fileMode: FileDialog.SaveFile
        nameFilters: ["JSON文件 (*.json)", "CSV文件 (*.csv)"]

        onAccepted: {
            var filePath = exportDialog.selectedFile
            var format = exportDialog.selectedNameFilter.includes("json") ? "json" : "csv"
            mainWindowBackend.export_applications(filePath, format)
        }
    }

    // 导入对话框
    FileDialog {
        id: importDialog
        title: "导入应用列表"
        fileMode: FileDialog.OpenFile
        nameFilters: ["JSON文件 (*.json)", "CSV文件 (*.csv)"]

        onAccepted: {
            var filePath = importDialog.selectedFile
            var format = importDialog.selectedNameFilter.includes("json") ? "json" : "csv"
            importApplications(filePath, format)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        // 搜索框
        Rectangle {
            id: searchBox
            Layout.fillWidth: true
            height: 40
            radius: 8
            color: "#F0F0F0"
            border.color: "#CCCCCC"
            border.width: 1

            // 搜索图标
            Text {
                id: searchIcon
                anchors.left: parent.left
                anchors.leftMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                text: "🔍"
                color: "#666"
                font.pixelSize: 16
            }

            // 搜索输入框
            TextField {
                id: searchInput
                anchors.left: searchIcon.right
                anchors.right: clearButton.left
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 5
                anchors.rightMargin: 5
                placeholderText: "搜索应用..."
                color: "#000"
                selectByMouse: true
                background: Rectangle {
                    color: "#F0F0F0"
                }

                onTextChanged: {
                    refreshAppList()
                }
            }

            // 清空按钮
            Rectangle {
                id: clearButton
                anchors.right: parent.right
                anchors.rightMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                width: 20
                height: 20
                radius: 10
                color: "#555"
                visible: searchInput.text !== ""

                Text {
                    anchors.centerIn: parent
                    text: "×"
                    color: "#000"
                    font.pixelSize: 14
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        searchInput.text = ""
                        searchInput.focus = true
                    }
                    cursorShape: Qt.PointingHandCursor
                }
            }
        }

        // 工具栏
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            // 添加应用按钮
            Rectangle {
                width: 100
                height: 40
                radius: 5
                color: "#4CAF50"

                Text {
                    anchors.centerIn: parent
                    text: "添加应用"
                    color: "white"
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        console.log("打开文件对话框")
                        var apps = mainWindowBackend.show_file_dialog()
                        if (apps && apps.length > 0) {
                            console.log("成功添加应用，数量:", apps.length)
                        }
                    }
                    cursorShape: Qt.PointingHandCursor
                }
            }

            // 编辑按钮
            Rectangle {
                id: editButton
                width: 80
                height: 40
                radius: 5
                color: appListView.selectedApps.count > 0 ? "#FF9800" : "#666"

                Text {
                    anchors.centerIn: parent
                    text: "编辑"
                    color: "#000"
                }

                MouseArea {
                    anchors.fill: parent
                    enabled: appListView.selectedApps.count === 1
                    onClicked: {
                        if (appListView.selectedApps.count === 1) {
                            var app = appListView.selectedApps.get(0)
                            appListView.currentAppId = app.id
                            editNameField.text = app.name
                            editDescField.text = app.description || ""
                            editDialog.open()
                        }
                    }
                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                }
            }

            // 删除选中按钮
            Rectangle {
                id: deleteButton
                width: 120
                height: 40
                radius: 5
                color: appListView.selectedApps.count > 0 ? "#F44336" : "#666"

                Text {
                    anchors.centerIn: parent
                    text: "🗑删除选中 (" + appListView.selectedApps.count + ")"
                    color: "#000"
                }

                MouseArea {
                    anchors.fill: parent
                    enabled: appListView.selectedApps.count > 0
                    onClicked: {
                        if (appListView.selectedApps.count > 0) {
                            confirmDialog.open()
                        }
                    }
                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                }
            }

            // 启动按钮
            Rectangle {
                id: launchButton
                width: 100
                height: 40
                radius: 5
                color: appListView.selectedApps.count === 1 ? "#2196F3" : "#666"

                Text {
                    anchors.centerIn: parent
                    text: "启动"
                    color: "#000"
                }

                MouseArea {
                    anchors.fill: parent
                    enabled: appListView.selectedApps.count === 1
                    onClicked: {
                        if (appListView.selectedApps.count === 1) {
                            var app = appListView.selectedApps.get(0)
                            mainWindowBackend.launch_application(app.id)
                        }
                    }
                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                }
            }

            // 导出按钮
            Rectangle {
                width: 100
                height: 40
                radius: 5
                color: "#9C27B0"

                Text {
                    anchors.centerIn: parent
                    text: "📤 导出"
                    color: "#000"
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        exportDialog.open()
                    }
                    cursorShape: Qt.PointingHandCursor
                }
            }

            // 导入按钮
            Rectangle {
                width: 100
                height: 40
                radius: 5
                color: "#FF9800"

                Text {
                    anchors.centerIn: parent
                    text: "📥 导入"
                    color: "#000"
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        importDialog.open()
                    }
                    cursorShape: Qt.PointingHandCursor
                }
            }

            // 刷新按钮
            Rectangle {
                width: 80
                height: 40
                radius: 5
                color: "#607D8B"

                Text {
                    anchors.centerIn: parent
                    text: "🔄 刷新"
                    color: "#000"
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        refreshAppList()
                    }
                    cursorShape: Qt.PointingHandCursor
                }
            }

            // 添加一个占位项
            Item {
                Layout.fillWidth: true
            }
        }

        // 应用列表
        Rectangle {
            id: listContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 5
            border.color: "#CCCCCC"
            border.width: 1

            ListView {
                id: appListView
                anchors.fill: parent
                anchors.margins: 2
                clip: true

                model: ListModel { id: appModel }

                // 存储选中的应用
                property ListModel selectedApps: ListModel {}
                property string currentAppId: ""

                delegate: Rectangle {
                    id: appDelegate
                    width: ListView.view.width-appListScrollbar.width
                    height: 70
                    color: isSelected ? "#094771" : (index % 2 ? "#F0F0F0" : "#E0E0E0")

                    // 选中效果
                    property bool isSelected: false

                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: isSelected ? "#4CAF50" : "transparent"
                        border.width: 2
                    }

                    Row {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 15

                        // 应用图标
                        Image {
                            id: appIcon
                            width: 48
                            height: 48
                            source: model.icon_path ? model.icon_path : ("image://icon/" + encodeURIComponent(model.path))
                            fillMode: Image.PreserveAspectFit
                            sourceSize.width: 48
                            sourceSize.height: 48

                            onStatusChanged: {
                                if (status === Image.Error) {
                                    console.log("图标加载失败:", model.path)
                                }
                            }
                        }

                        Column {
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 4
                            width: parent.width - appIcon.width - 150

                            Text {
                                text: model.name || "未命名应用"
                                color: "#000"
                                font.pixelSize: 14
                                font.bold: true
                                elide: Text.ElideRight
                                width: parent.width
                            }

                            Text {
                                text: model.path || "未知路径"
                                color: "#666666"
                                font.pixelSize: 10
                                elide: Text.ElideRight
                                width: parent.width
                            }

                            Text {
                                text: model.description || "无描述"
                                color: "#888888"
                                font.pixelSize: 10
                                elide: Text.ElideRight
                                width: parent.width
                                visible: model.description && model.description !== ""
                            }

                            Row {
                                spacing: 10
                                visible: model.last_used > 0 || model.usage_count > 0

                                Text {
                                    text: "使用: " + (model.usage_count || 0) + " 次"
                                    color: "#000"
                                    font.pixelSize: 9
                                }

                                Text {
                                    text: "最后使用: " + formatDate(model.last_used)
                                    color: "#000"
                                    font.pixelSize: 9
                                    visible: model.last_used > 0
                                }
                            }
                        }


                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: function(mouse) {
                            console.log("点击应用: " + model.name + ", ID: " + model.id)

                            if (mouse.modifiers & Qt.ControlModifier) {
                                // Ctrl+点击：多选
                                toggleSelection()
                            } else if (mouse.modifiers & Qt.ShiftModifier) {
                                // Shift+点击：范围选择
                                // 这里可以添加范围选择逻辑
                            } else {
                                // 普通点击：单选
                                clearSelections()
                                toggleSelection()
                            }
                        }

                        onDoubleClicked: {
                            // 双击启动应用
                            mainWindowBackend.launch_application(model.id)
                        }
                    }

                    // 选择/取消选择函数
                    function toggleSelection() {
                        isSelected = !isSelected

                        if (isSelected) {
                            // 添加到选中列表
                            appListView.selectedApps.append({
                                id: model.id,
                                name: model.name,
                                description: model.description,
                                path: model.path
                            })
                        } else {
                            // 从选中列表移除
                            for (var i = 0; i < appListView.selectedApps.count; i++) {
                                if (appListView.selectedApps.get(i).id === model.id) {
                                    appListView.selectedApps.remove(i)
                                    break
                                }
                            }
                        }
                    }

                    function clearSelections() {
                        // 清空所有选择
                        for (var i = 0; i < appListView.selectedApps.count; i++) {
                            var appId = appListView.selectedApps.get(i).id
                            // 找到对应的delegate并取消选择
                            for (var j = 0; j < appListView.contentItem.children.length; j++) {
                                var child = appListView.contentItem.children[j]
                                if (child.model && child.model.id === appId) {
                                    child.isSelected = false
                                    break
                                }
                            }
                        }
                        appListView.selectedApps.clear()
                    }
                }

                // 如果没有应用
                Rectangle {
                    anchors.centerIn: parent
                    width: 400
                    height: 200
                    color: "transparent"
                    visible: appModel.count === 0

                    Column {
                        anchors.centerIn: parent
                        spacing: 20

                        Text {
                            text: ""
                            color: "#666"
                            font.pixelSize: 48
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        Text {
                            text: "暂无应用"
                            color: "#666"
                            font.pixelSize: 18
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        Text {
                            text: "点击\"添加应用\"按钮开始添加应用"
                            color: "#000"
                            font.pixelSize: 14
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        Rectangle {
                            width: 200
                            height: 40
                            radius: 5
                            color: "#007ACC"
                            anchors.horizontalCenter: parent.horizontalCenter

                            Text {
                                anchors.centerIn: parent
                                text: "➕ 添加应用"
                                color: "#000"
                                font.pixelSize: 14
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    var apps = mainWindowBackend.show_file_dialog()
                                    if (apps && apps.length > 0) {
                                        refreshAppList()
                                    }
                                }
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                    }
                }

                // 滚动条 - 优化样式
                ScrollBar.vertical: ScrollBar {
                    id: appListScrollbar
                    policy: ScrollBar.AlwaysOn
                    width: 12
                    
                    background: Rectangle {
                        anchors.margins: 0
                        color: "#ffffff"  // 透明背景以避免黑色背景问题


                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 0
                            color:  "#ffffff"// 使用与容器相同的背景色

                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: 0  // 完全填满，无边距
                                color: "#ffffff"
                                visible: appListScrollbar.size < 1.0
                            }
                        }
                    }
                    
                    contentItem: Rectangle {
                        implicitWidth: 12
                        implicitHeight: 30
                        radius: 6
                        color: "#b8b8b8"
                        
                        states: State {
                            when: appListScrollbar.pressed
                            PropertyChanges {
                                target: appListScrollbar.contentItem
                                color: "#ffffff"
                            }
                        }
                        
                        transitions: Transition {
                            from: "*"; to: "pressed"
                            NumberAnimation { 
                                properties: "color"; 
                                duration: 100 
                                easing.type: Easing.InOutCubic 
                            }
                        }
                    }
                }
            }

            // 选中计数
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.margins: 5
                width: selectedCountLabel.width + 20
                height: 25
                radius: 3
                color: "#094771"
                visible: appListView.selectedApps.count > 0
                opacity: 0.9

                Text {
                    id: selectedCountLabel
                    anchors.centerIn: parent
                    text: "已选中: " + appListView.selectedApps.count + " / " + appModel.count
                    color: "#000"
                    font.pixelSize: 12
                }
            }

            // 统计信息
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.margins: 5
                width: statsLabel.width + 20
                height: 25
                radius: 3
                color: "#F0F0F0"
                opacity: 0.8

                Text {
                    id: statsLabel
                    anchors.centerIn: parent
                    text: "应用统计"
                    color: "#000"
                    font.pixelSize: 12
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor

                    onEntered: {
                        parent.color = "#E0E0E0"
                    }
                    onExited: {
                        parent.color = "#F0F0F0"
                    }
                    onClicked: {
                        showStatsDialog()
                    }
                }
            }
        }
    }

    // 刷新应用列表函数
    function refreshAppList() {
        try {
            var query = searchInput.text
            var apps

            if (query) {
                apps = mainWindowBackend.search_applications(query)
            } else {
                apps = mainWindowBackend.get_applications()
            }

            console.log("刷新应用列表，数量:", apps.length)

            // 保存当前选中状态
            var selectedIds = []
            for (var i = 0; i < appListView.selectedApps.count; i++) {
                selectedIds.push(appListView.selectedApps.get(i).id)
            }

            // 清空并重新填充模型
            appModel.clear()
            for (var i = 0; i < apps.length; i++) {
                var app = apps[i]
                // 确保每个应用都有必需的字段
                if (!app.icon_path) {
                    app.icon_path = "image://icon/" + encodeURIComponent(app.path)
                }
                appModel.append(app)
            }

            // 恢复选中状态
            appListView.selectedApps.clear()
            for (var j = 0; j < selectedIds.length; j++) {
                for (var k = 0; k < appModel.count; k++) {
                    if (appModel.get(k).id === selectedIds[j]) {
                        appListView.selectedApps.append(appModel.get(k))
                        break
                    }
                }
            }

        } catch (e) {
            console.log("刷新应用列表时出错:", e)
            // 使用正确的信号方法
            mainWindowBackend.show_message("错误", "刷新应用列表失败: " + e, "error")
        }
    }

    // 删除选中应用函数
    function deleteSelectedApps() {
        // 收集选中的应用ID
        var appIds = []
        var appNames = []
        for (var i = 0; i < appListView.selectedApps.count; i++) {
            appIds.push(appListView.selectedApps.get(i).id)
            appNames.push(appListView.selectedApps.get(i).name)
        }

        // 调用后端删除功能
        if (mainWindowBackend.remove_applications(appIds)) {
            console.log("删除成功，删除数量:", appIds.length)
            // 刷新列表
            refreshAppList()
            // 清空选中列表
            appListView.selectedApps.clear()
        } else {
            console.log("删除失败")
            mainWindowBackend.show_message("错误", "删除应用失败", "error")
        }
    }

    // 导入应用函数
    function importApplications(filePath, format) {
        console.log("开始导入应用:", filePath, format)
        mainWindowBackend.import_applications(filePath, format)
    }

    // 显示统计信息对话框
    function showStatsDialog() {
        var stats = mainWindowBackend.get_app_stats()
        var message = "应用统计信息:\n\n"
        message += "总应用数: " + stats.total_apps + "\n"
        message += "最近使用（7天内）: " + stats.recent_apps + "\n"
        message += "总使用次数: " + stats.total_usage + "\n"
        message += "最常用应用: " + (stats.most_used || "无") + "\n"
        message += "最高使用次数: " + stats.max_usage + "\n"

        mainWindowBackend.show_message("应用统计", message, "info")
    }

    // 格式化日期
    function formatDate(timestamp) {
        if (!timestamp || timestamp <= 0) {
            return "从未使用"
        }

        var date = new Date(timestamp * 1000)
        var now = new Date()
        var diff = Math.floor((now - date) / 1000)

        if (diff < 60) {
            return "刚刚"
        } else if (diff < 3600) {
            return Math.floor(diff / 60) + "分钟前"
        } else if (diff < 86400) {
            return Math.floor(diff / 3600) + "小时前"
        } else if (diff < 2592000) {
            return Math.floor(diff / 86400) + "天前"
        } else {
            return date.toLocaleDateString()
        }
    }

    // 连接后端信号 - 使用正确的信号名称
    Connections {
        target: mainWindowBackend

        // 注意：信号名称必须与Python后端完全匹配（下划线格式）
        function onApp_list_updated(apps) {
            console.log("收到应用列表更新信号")
            refreshAppList()
        }

        function onOperation_status(operation, message) {
            console.log("操作状态:", operation, message)
            if (operation === "add" || operation === "remove" || operation === "update") {
                refreshAppList()
            }
        }

        function onShow_message(title, message, type) {
            console.log("显示消息:", title, message, type)
        }
    }

    // 初始化应用列表
    Component.onCompleted: {
        console.log("AppManagement组件加载完成")
        refreshAppList()
    }
}