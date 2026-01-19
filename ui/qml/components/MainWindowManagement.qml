import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: mainWindowManagement
    anchors.fill: parent

    property var mainWindowConfig: ({})

    // 颜色选择对话框
    ColorDialog {
        id: colorDialog
        title: "选择背景颜色"
        onAccepted: {
            console.log("选择的颜色: " + colorDialog.color)
            var hexColor = "#" + colorDialog.color.toString().substring(3)  // 转换为标准十六进制格式
            console.log("转换后的十六进制颜色: " + hexColor)
            mainWindowBackend.update_main_window_config("background_color", hexColor)
            mainWindowConfig.background_color = hexColor
            console.log("背景颜色已更新: " + hexColor)
        }
        onRejected: {
            console.log("颜色选择已取消")
        }
    }

    // 图片文件选择对话框
    FileDialog {
        id: imageFileDialog
        title: "选择图片"
        currentFolder: StandardPaths.standardLocations(StandardPaths.PicturesLocation)[0]
        nameFilters: ["图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)", "所有文件 (*.*)"]
        fileMode: FileDialog.OpenFile
        onAccepted: {
            console.log("【QML DEBUG】开始上传背景图片: " + imageFileDialog.file)
            try {
                // 检查mainWindowBackend对象是否存在
                if (typeof mainWindowBackend === 'undefined' || mainWindowBackend === null) {
                    console.error("【QML DEBUG】mainWindowBackend对象未定义或为null")
                    return
                }else
                {
                    console.log("【QML DEBUG】mainWindowBackend存在")
                }
                
                // 检查upload_background_image方法是否存在
                if (typeof mainWindowBackend.upload_background_image !== 'function') {
                    console.error("【QML DEBUG】upload_background_image方法不存在")
                    return
                }
                
                console.log("【QML DEBUG】开始上传背景图片: " + imageFileDialog.file)
                // 使用decodeURIComponent来处理可能包含特殊字符的路径
                var fileUrl = imageFileDialog.file.toString()
                var imagePath = ""
                
                if (fileUrl.startsWith("file://")) {
                    imagePath = decodeURIComponent(fileUrl.substring(7))  // 移除 "file://" 前缀
                    // 在Windows系统上，可能需要将/转换为\
                    if (Qt.platform.os === "windows") {
                        imagePath = imagePath.replace(/\//g, "\\")
                    }
                    console.log("【QML DEBUG】解码后的图片路径: " + imagePath)
                } else {
                    imagePath = fileUrl
                }
                
                console.log("【QML DEBUG】处理后的图片路径: " + imagePath)
                console.log("【QML DEBUG】当前配置: " + JSON.stringify(mainWindowConfig))
                
                var result = mainWindowBackend.upload_background_image(imagePath)
                
                console.log("【QML DEBUG】上传结果: " + JSON.stringify(result))
                
                if (result.success) {
                    // 背景图片路径已在Python后端更新并发出配置更新信号
                    backgroundImageLabel.text = result.path
                    // 同时更新本地mainWindowConfig属性，以便保存配置时使用正确的值
                    if (mainWindowConfig === undefined || mainWindowConfig === null) {
                        mainWindowConfig = {};
                    }
                    mainWindowConfig.background_image = result.path;
                    mainWindowBackend.showMessage("成功", result.message, "success")
                    console.log("【QML DEBUG】背景图片上传并设置成功: " + result.path)
                    
                    // 发出配置更新信号以确保界面同步
                    console.log("【QML DEBUG】发出配置更新信号...")
                    // 注意：配置更新信号由Python后端自动发出，不需要在此处手动发出
                } else {
                    mainWindowBackend.showMessage("错误", result.message, "error")
                    console.log("【QML DEBUG】背景图片上传失败: " + result.message)
                }
            } catch (error) {
                console.error("【QML DEBUG】上传背景图片时发生错误: " + error)
                console.error("【QML DEBUG】错误堆栈: " + error.stack)
                console.error("【QML DEBUG】错误名称: " + error.name)
                console.error("【QML DEBUG】错误信息: " + error.message)
                mainWindowBackend.showMessage("错误", "上传背景图片时发生错误: " + error, "error")
            }
        }
        onRejected: {
            console.log("【QML DEBUG】用户取消了图片选择")
        }
    }

    // 更新背景图片文件对话框
    FileDialog {
        id: updateImageFileDialog
        title: "选择新的背景图片"
        currentFolder: StandardPaths.standardLocations(StandardPaths.PicturesLocation)[0]
        nameFilters: ["图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)", "所有文件 (*.*)"]
        fileMode: FileDialog.OpenFile
        options: FileDialog.DontUseNativeDialog  // 使用Qt的对话框而不是系统原生对话框
        onAccepted: {
            console.log("【QML DEBUG】开始更新背景图片: " + updateImageFileDialog.file)
            try {
                // 检查mainWindowBackend对象是否存在
                if (typeof mainWindowBackend === 'undefined' || mainWindowBackend === null) {
                    console.error("【QML DEBUG】mainWindowBackend对象未定义或为null")
                    return
                }
                
                // 检查update_background_image方法是否存在
                if (typeof mainWindowBackend.update_background_image !== 'function') {
                    console.error("【QML DEBUG】update_background_image方法不存在")
                    console.log("【QML DEBUG】尝试使用upload_background_image方法...")
                    // 如果update_background_image不存在，则使用upload_background_image
                    if (typeof mainWindowBackend.upload_background_image !== 'function') {
                        console.error("【QML DEBUG】upload_background_image方法也不存在")
                        return
                    }
                }
                
                console.log("【QML DEBUG】开始更新背景图片: " + updateImageFileDialog.file)
                // 使用decodeURIComponent来处理可能包含特殊字符的路径
                var fileUrl = updateImageFileDialog.file.toString()
                var imagePath = ""
                
                if (fileUrl.startsWith("file://")) {
                    imagePath = decodeURIComponent(fileUrl.substring(7))  // 移除 "file://" 前缀
                    // 在Windows系统上，可能需要将/转换为\
                    if (Qt.platform.os === "windows") {
                        imagePath = imagePath.replace(/\//g, "\\")
                    }
                    console.log("【QML DEBUG】解码后的图片路径: " + imagePath)
                } else {
                    imagePath = fileUrl
                }
                
                console.log("【QML DEBUG】处理后的图片路径: " + imagePath)
                mainWindowConfig = mainWindowBackend.get_main_window_config()
                console.log("【QML DEBUG】当前配置: " + JSON.stringify(mainWindowConfig))
                
                // 根据后端是否支持update_background_image方法来调用
                var result;
                if (typeof mainWindowBackend.update_background_image === 'function') {
                    result = mainWindowBackend.update_background_image(imagePath)
                } else {
                    result = mainWindowBackend.upload_background_image(imagePath)
                }
                
                console.log("【QML DEBUG】更新结果: " + JSON.stringify(result))
                
                if (result.success) {
                    // 背景图片路径已在Python后端更新并发出配置更新信号
                    backgroundImageLabel.text = result.path
                    // 同时更新本地mainWindowConfig属性，以便保存配置时使用正确的值
                    if (mainWindowConfig === undefined || mainWindowConfig === null) {
                        mainWindowConfig = {};
                    }
                    mainWindowConfig.background_image = result.path;
                    mainWindowBackend.showMessage("成功", result.message, "success")
                    console.log("【QML DEBUG】背景图片更新并设置成功: " + result.path)
                    
                    // 发出配置更新信号以确保界面同步
                    console.log("【QML DEBUG】发出配置更新信号...")
                } else {
                    mainWindowBackend.showMessage("错误", result.message, "error")
                    console.log("【QML DEBUG】背景图片更新失败: " + result.message)
                }
            } catch (error) {
                console.error("【QML DEBUG】更新背景图片时发生错误: " + error)
                console.error("【QML DEBUG】错误堆栈: " + error.stack)
                console.error("【QML DEBUG】错误名称: " + error.name)
                console.error("【QML DEBUG】错误信息: " + error.message)
                mainWindowBackend.showMessage("错误", "更新背景图片时发生错误: " + error, "error")
            }
        }
        onRejected: {
            console.log("【QML DEBUG】用户取消了图片选择")
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        // 主窗口设置区域
        GroupBox {
            id: settingsGroup
            Layout.fillWidth: true
            Layout.preferredHeight: 500
            title: "主窗口设置"
            background: Rectangle {
                color: "#FFFFFF"
                border.color: "#CCCCCC"
                border.width: 1
                radius: 8
            }

            label: Label {
                text: "主窗口设置"
                color: "#000"
                font.pixelSize: 14
                font.bold: true
                leftPadding: 10
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 15

                // 背景图片上传
                RowLayout {
                    spacing: 10

                    Text {
                        text: "背景图片:"
                        Layout.minimumWidth: 80
                        color: "#000"
                    }

                    // 带有背景图片预览的按钮
                    Item {
                        id: imagePreviewButton
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 80
                        
                        Rectangle {
                            anchors.fill: parent
                            radius: 4
                            border.color: "#999"
                            border.width: 1
                            color: mainWindowConfig.background_image && mainWindowConfig.background_image !== "" ? "transparent" : "#f0f0f0"
                        }
                        
                        Image {
                            anchors.fill: parent
                            anchors.margins: 1
                            source: mainWindowConfig.background_image ? "file://" + mainWindowConfig.background_image : ""
                            fillMode: Image.PreserveAspectCrop
                            clip: true
                            visible: mainWindowConfig.background_image && mainWindowConfig.background_image !== ""
                            
                            // 图片加载错误处理
                            onStatusChanged: {
                                if (status === Image.Error) {
                                    console.log("预览图片加载失败: " + source)
                                }
                            }
                        }
                        
                        Text {
                            anchors.centerIn: parent
                            text: mainWindowConfig.background_image && mainWindowConfig.background_image !== "" ? 
                                  (mainWindowConfig.background_image ? "更换图片" : "") : "选择图片"
                            color: "#666"
                            font.pixelSize: 12
                            visible: !(mainWindowConfig.background_image && mainWindowConfig.background_image !== "")
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                console.log("【QML DEBUG】点击了" + (mainWindowConfig.background_image && mainWindowConfig.background_image !== "" ? "更换图片" : "选择图片") + "按钮")
                                if (mainWindowConfig.background_image && mainWindowConfig.background_image !== "") {
                                    updateImageFileDialog.open()
                                } else {
                                    imageFileDialog.open()
                                }
                            }
                            cursorShape: Qt.PointingHandCursor
                        }
                    }

                    Text {
                        id: backgroundImageLabel
                        Layout.fillWidth: true
                        text: mainWindowConfig.background_image ? mainWindowConfig.background_image : "未选择图片"
                        color: "#000"
                        font.pixelSize: 12
                        elide: Text.ElideRight
                    }

                    Button {
                        text: "信息"
                        Layout.preferredWidth: 60
                        enabled: mainWindowConfig.background_image && mainWindowConfig.background_image !== ""

                        onClicked: {
                            try {
                                console.log("获取背景图片信息");
                                // 修复：只有在background_image有效时才调用get_image_info
                                if (mainWindowConfig.background_image && mainWindowConfig.background_image !== "" && mainWindowConfig.background_image !== "undefined") {
                                    var result = mainWindowBackend.get_image_info("file://" + mainWindowConfig.background_image)
                                    if (result.success) {
                                        var infoText = "图片信息: " + result.width + "x" + result.height + ", 格式: " + result.format + ", 大小: " + Math.round(result.size_bytes/1024) + "KB"
                                        console.log(infoText);
                                        mainWindowBackend.showMessage("图片信息", infoText, "info")
                                    } else {
                                        mainWindowBackend.showMessage("错误", result.message, "error")
                                        console.log("获取图片信息失败: " + result.message);
                                    }
                                } else {
                                    mainWindowBackend.showMessage("错误", "当前没有设置背景图片", "error")
                                    console.log("当前没有设置背景图片或图片路径无效");
                                }
                            } catch (error) {
                                console.error("获取图片信息时发生错误: " + error);
                                mainWindowBackend.showMessage("错误", "获取图片信息时发生错误: " + error, "error");
                            }
                        }
                    }

                    Button {
                        text: "优化"
                        Layout.preferredWidth: 60
                        enabled: mainWindowConfig.background_image && mainWindowConfig.background_image !== ""

                        onClicked: {
                            try {
                                console.log("优化当前背景图片");
                                var result = mainWindowBackend.optimize_current_background_image()
                                if (result.success) {
                                    console.log("背景图片已优化: " + result.message);
                                    if (result.path) {
                                        backgroundImageLabel.text = result.path
                                    }
                                    mainWindowBackend.showMessage("成功", result.message, "success")
                                } else {
                                    mainWindowBackend.showMessage("错误", result.message, "error")
                                    console.log("优化背景图片失败: " + result.message);
                                }
                            } catch (error) {
                                console.error("优化背景图片时发生错误: " + error);
                                mainWindowBackend.showMessage("错误", "优化背景图片时发生错误: " + error, "error");
                            }
                        }
                    }

                    Button {
                        text: "清除"
                        Layout.preferredWidth: 60

                        onClicked: {
                            try {
                                console.log("清除背景图片");
                                mainWindowConfig = mainWindowBackend.get_main_window_config()
                                var result = mainWindowBackend.clear_background_image()
                                if (result.success) {
                                    backgroundImageLabel.text = "未选择图片"
                                    // 同时更新本地mainWindowConfig变量，以便保存配置时使用正确的值
                                    if (mainWindowConfig === undefined || mainWindowConfig === null) {
                                        mainWindowConfig = {};
                                    }
                                    mainWindowConfig.background_image = "";
                                    console.log("背景图片已清除");
                                } else {
                                    mainWindowBackend.showMessage("错误", result.message, "error")
                                    console.log("清除背景图片失败: " + result.message);
                                }
                            } catch (error) {
                                console.error("清除背景图片时发生错误: " + error);
                                mainWindowBackend.showMessage("错误", "清除背景图片时发生错误: " + error, "error");
                            }
                        }
                    }
                }

                // 模糊半径设置 - 毛玻璃效果的主要参数
                RowLayout {
                    spacing: 10

                    Text {
                        text: "模糊半径:"
                        Layout.minimumWidth: 80
                        color: "#000"
                    }

                    Slider {
                        id: radiusBlurSlider
                        Layout.fillWidth: true
                        from: 0
                        to: 100
                        value: 20
                        stepSize: 1

                        background: Rectangle {
                            x: radiusBlurSlider.leftPadding
                            y: radiusBlurSlider.topPadding + radiusBlurSlider.availableHeight / 2 - height / 2
                            implicitWidth: 200
                            implicitHeight: 4
                            width: radiusBlurSlider.availableWidth
                            height: implicitHeight
                            radius: 2
                            color: "#444"

                            Rectangle {
                                width: radiusBlurSlider.visualPosition * parent.width
                                height: parent.height
                                color: "#9C27B0"
                                radius: 2
                            }
                        }

                        handle: Rectangle {
                            x: radiusBlurSlider.leftPadding + radiusBlurSlider.visualPosition * (radiusBlurSlider.availableWidth - width)
                            y: radiusBlurSlider.topPadding + radiusBlurSlider.availableHeight / 2 - height / 2
                            implicitWidth: 16
                            implicitHeight: 16
                            radius: 8
                            color: radiusBlurSlider.pressed ? "#7B1FA2" : "#9C27B0"
                            border.color: "#BDBDBD"
                        }

                        onValueChanged: {
                            mainWindowBackend.update_main_window_config("radius_blur", Math.round(value))
                        }
                    }

                    Text {
                        text: radiusBlurSlider.value + "px"
                        Layout.minimumWidth: 40
                        color: "#000"
                        font.pixelSize: 12
                    }
                }

                // 背景毛玻璃透明度设置（磨砂质感）
                RowLayout {
                    spacing: 10

                    Text {
                        text: "磨砂透明度:"
                        Layout.minimumWidth: 80
                        color: "#000"
                    }

                    Slider {
                        id: backgroundOpacitySlider
                        Layout.fillWidth: true
                        from: 0.0
                        to: 1.0
                        value: 0.3
                        stepSize: 0.05

                        background: Rectangle {
                            x: backgroundOpacitySlider.leftPadding
                            y: backgroundOpacitySlider.topPadding + backgroundOpacitySlider.availableHeight / 2 - height / 2
                            implicitWidth: 200
                            implicitHeight: 4
                            width: backgroundOpacitySlider.availableWidth
                            height: implicitHeight
                            radius: 2
                            color: "#444"

                            Rectangle {
                                width: backgroundOpacitySlider.visualPosition * parent.width
                                height: parent.height
                                color: "#80CBC4"
                                radius: 2
                            }
                        }

                        handle: Rectangle {
                            x: backgroundOpacitySlider.leftPadding + backgroundOpacitySlider.visualPosition * (backgroundOpacitySlider.availableWidth - width)
                            y: backgroundOpacitySlider.topPadding + backgroundOpacitySlider.availableHeight / 2 - height / 2
                            implicitWidth: 16
                            implicitHeight: 16
                            radius: 8
                            color: backgroundOpacitySlider.pressed ? "#00796B" : "#009688"
                            border.color: "#BDBDBD"
                        }

                        onValueChanged: {
                            mainWindowBackend.update_main_window_config("background_opacity", value)
                        }
                    }

                    Text {
                        text: Math.round(backgroundOpacitySlider.value * 100) + "%"
                        Layout.minimumWidth: 40
                        color: "#000"
                        font.pixelSize: 12
                    }
                }

                // 着色透明度设置 - 控制毛玻璃色调透明度
                RowLayout {
                    spacing: 10

                    Text {
                        text: "色调透明度:"
                        Layout.minimumWidth: 80
                        color: "#000"
                    }

                    Slider {
                        id: opacityTintSlider
                        Layout.fillWidth: true
                        from: 0.0
                        to: 1.0
                        value: 0.15
                        stepSize: 0.05

                        background: Rectangle {
                            x: opacityTintSlider.leftPadding
                            y: opacityTintSlider.topPadding + opacityTintSlider.availableHeight / 2 - height / 2
                            implicitWidth: 200
                            implicitHeight: 4
                            width: opacityTintSlider.availableWidth
                            height: implicitHeight
                            radius: 2
                            color: "#444"

                            Rectangle {
                                width: opacityTintSlider.visualPosition * parent.width
                                height: parent.height
                                color: "#FF9800"
                                radius: 2
                            }
                        }

                        handle: Rectangle {
                            x: opacityTintSlider.leftPadding + opacityTintSlider.visualPosition * (opacityTintSlider.availableWidth - width)
                            y: opacityTintSlider.topPadding + opacityTintSlider.availableHeight / 2 - height / 2
                            implicitWidth: 16
                            implicitHeight: 16
                            radius: 8
                            color: opacityTintSlider.pressed ? "#F57C00" : "#FF9800"
                            border.color: "#BDBDBD"
                        }

                        onValueChanged: {
                            mainWindowBackend.update_main_window_config("opacity_tint", value)
                        }
                    }

                    Text {
                        text: Math.round(opacityTintSlider.value * 100) + "%"
                        Layout.minimumWidth: 40
                        color: "#000"
                        font.pixelSize: 12
                    }
                }

                // 噪声透明度设置 - 控制毛玻璃噪声效果
                RowLayout {
                    spacing: 10

                    Text {
                        text: "噪声透明度:"
                        Layout.minimumWidth: 80
                        color: "#000"
                    }

                    Slider {
                        id: opacityNoiseSlider
                        Layout.fillWidth: true
                        from: 0.0
                        to: 0.2
                        value: 0.02
                        stepSize: 0.005

                        background: Rectangle {
                            x: opacityNoiseSlider.leftPadding
                            y: opacityNoiseSlider.topPadding + opacityNoiseSlider.availableHeight / 2 - height / 2
                            implicitWidth: 200
                            implicitHeight: 4
                            width: opacityNoiseSlider.availableWidth
                            height: implicitHeight
                            radius: 2
                            color: "#444"

                            Rectangle {
                                width: opacityNoiseSlider.visualPosition * parent.width
                                height: parent.height
                                color: "#4CAF50"
                                radius: 2
                            }
                        }

                        handle: Rectangle {
                            x: opacityNoiseSlider.leftPadding + opacityNoiseSlider.visualPosition * (opacityNoiseSlider.availableWidth - width)
                            y: opacityNoiseSlider.topPadding + opacityNoiseSlider.availableHeight / 2 - height / 2
                            implicitWidth: 16
                            implicitHeight: 16
                            radius: 8
                            color: opacityNoiseSlider.pressed ? "#388E3C" : "#4CAF50"
                            border.color: "#BDBDBD"
                        }

                        onValueChanged: {
                            mainWindowBackend.update_main_window_config("opacity_noise", value)
                        }
                    }

                    Text {
                        text: Math.round(opacityNoiseSlider.value * 1000) + "‰"
                        Layout.minimumWidth: 40
                        color: "#000"
                        font.pixelSize: 12
                    }
                }

                // 背景颜色设置 - 控制毛玻璃基础色调
                RowLayout {
                    spacing: 10

                    Text {
                        text: "背景颜色:"
                        Layout.minimumWidth: 80
                        color: "#000"
                    }

                    Rectangle {
                        width: 50
                        height: 30
                        color: mainWindowConfig.background_color ? mainWindowConfig.background_color : "#FFFFFF"
                        border.color: "#CCCCCC"
                        border.width: 1
                        radius: 4

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                // 这里可以打开颜色选择对话框
                                // 目前暂时使用默认颜色
                                var newColor = "#FFFFFF" // 示例颜色
                                mainWindowBackend.update_main_window_config("background_color", newColor)
                                mainWindowConfig.background_color = newColor
                            }
                        }
                    }

                    Text {
                        text: mainWindowConfig.background_color ? mainWindowConfig.background_color : "#FFFFFF"
                        Layout.fillWidth: true
                        color: "#000"
                        font.pixelSize: 12
                    }
                }

                // 亮度设置 - 控制毛玻璃亮度
                RowLayout {
                    spacing: 10

                    Text {
                        text: "亮度:"
                        Layout.minimumWidth: 80
                        color: "#000"
                    }

                    Slider {
                        id: luminositySlider
                        Layout.fillWidth: true
                        from: 0.0
                        to: 1.0
                        value: 0.1
                        stepSize: 0.01

                        background: Rectangle {
                            x: luminositySlider.leftPadding
                            y: luminositySlider.topPadding + luminositySlider.availableHeight / 2 - height / 2
                            implicitWidth: 200
                            implicitHeight: 4
                            width: luminositySlider.availableWidth
                            height: implicitHeight
                            radius: 2
                            color: "#444"

                            Rectangle {
                                width: luminositySlider.visualPosition * parent.width
                                height: parent.height
                                color: "#2196F3"
                                radius: 2
                            }
                        }

                        handle: Rectangle {
                            x: luminositySlider.leftPadding + luminositySlider.visualPosition * (luminositySlider.availableWidth - width)
                            y: luminositySlider.topPadding + luminositySlider.availableHeight / 2 - height / 2
                            implicitWidth: 16
                            implicitHeight: 16
                            radius: 8
                            color: luminositySlider.pressed ? "#1976D2" : "#2196F3"
                            border.color: "#BDBDBD"
                        }

                        onValueChanged: {
                            mainWindowBackend.update_main_window_config("luminosity", value)
                        }
                    }

                    Text {
                        text: Math.round(luminositySlider.value * 100) + "%"
                        Layout.minimumWidth: 40
                        color: "#000"
                        font.pixelSize: 12
                    }
                }

                // 噪声效果开关
                RowLayout {
                    spacing: 10

                    Text {
                        text: "启用噪声:"
                        Layout.minimumWidth: 80
                        color: "#000"
                    }

                    Switch {
                        id: enableNoiseSwitch
                        checked: true

                        onCheckedChanged: {
                            mainWindowBackend.update_main_window_config("enable_noise", checked)
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                    }
                }

                // 重置和保存按钮
                RowLayout {
                    spacing: 10
                    Layout.alignment: Qt.AlignRight

                    Item {
                        Layout.fillWidth: true
                    }

                    // 重置按钮
                    Rectangle {
                        width: 100
                        height: 30
                        radius: 5
                        color: "#F44336"

                        Text {
                            anchors.centerIn: parent
                            text: "重置"
                            color: "white"
                            font.pixelSize: 12
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                resetToDefaults()
                            }
                            cursorShape: Qt.PointingHandCursor
                        }
                    }

                    // 保存按钮
                    Rectangle {
                        width: 100
                        height: 30
                        radius: 5
                        color: "#4CAF50"

                        Text {
                            anchors.centerIn: parent
                            text: "保存配置"
                            color: "white"
                            font.pixelSize: 12
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
        }

        Item {
            Layout.fillHeight: true
        }
    }

    // 初始化配置
    Component.onCompleted: {
        console.log("MainWindowManagement组件加载完成")
        // 首先从后端获取最新的配置
        var initialConfig = mainWindowBackend.get_main_window_config();
        console.log("获取到初始配置:", JSON.stringify(initialConfig))
        // 确保mainWindowConfig已初始化
        if (!mainWindowConfig || typeof mainWindowConfig !== 'object') {
            mainWindowConfig = {};
        }
        // 将后端配置复制到本地变量
        for (var key in initialConfig) {
            mainWindowConfig[key] = initialConfig[key];
        }
        loadConfig();
    }

    // 加载配置
    function loadConfig() {
        try {

            console.log("加载主窗口配置:", JSON.stringify(mainWindowConfig))

            // 设置控件值
            if (mainWindowConfig.background_image !== undefined && mainWindowConfig.background_image !== null) {
                backgroundImageLabel.text = mainWindowConfig.background_image ? mainWindowConfig.background_image : "未选择图片"
                // 确保在配置更新时正确设置图片预览
                if (mainWindowConfig.background_image) {
                    imagePreviewButton.children[0].color = "transparent";  // 透明背景，显示图片
                } else {
                    imagePreviewButton.children[0].color = "#f0f0f0";  // 灰色背景，显示文字
                }
            }
            if (mainWindowConfig.radius_blur !== undefined && mainWindowConfig.radius_blur !== null) {
                radiusBlurSlider.value = mainWindowConfig.radius_blur
            } else {
                radiusBlurSlider.value = 20  // 默认值
            }
            if (mainWindowConfig.background_opacity !== undefined && mainWindowConfig.background_opacity !== null) {
                backgroundOpacitySlider.value = mainWindowConfig.background_opacity
            } else {
                backgroundOpacitySlider.value = 0.3  // 默认值
            }
            if (mainWindowConfig.opacity_tint !== undefined && mainWindowConfig.opacity_tint !== null) {
                opacityTintSlider.value = mainWindowConfig.opacity_tint
            } else {
                opacityTintSlider.value = 0.15  // 默认值
            }
            if (mainWindowConfig.opacity_noise !== undefined && mainWindowConfig.opacity_noise !== null) {
                opacityNoiseSlider.value = mainWindowConfig.opacity_noise
            } else {
                opacityNoiseSlider.value = 0.02  // 默认值
            }
            if (mainWindowConfig.background_color !== undefined && mainWindowConfig.background_color !== null) {
                // 颜色设置已经在界面上显示
            } else {
                // 默认颜色设置
            }
            if (mainWindowConfig.luminosity !== undefined && mainWindowConfig.luminosity !== null) {
                luminositySlider.value = mainWindowConfig.luminosity
            } else {
                luminositySlider.value = 0.1  // 默认值
            }
            if (mainWindowConfig.enable_noise !== undefined && mainWindowConfig.enable_noise !== null) {
                enableNoiseSwitch.checked = mainWindowConfig.enable_noise
            } else {
                enableNoiseSwitch.checked = true  // 默认值
            }
        } catch (error) {
            console.error("加载配置失败: " + error)
            console.error("错误堆栈: " + error.stack)
            mainWindowBackend.showMessage("错误", "加载配置失败: " + error, "error")
        }
    }

    // 保存所有配置
    function saveAllConfig() {
        // 保存当前配置
        mainWindowBackend.update_main_window_config("background_image", mainWindowConfig.background_image)
        mainWindowBackend.update_main_window_config("radius_blur", parseInt(radiusBlurSlider.value))
        mainWindowBackend.update_main_window_config("background_opacity", parseFloat(backgroundOpacitySlider.value))
        mainWindowBackend.update_main_window_config("opacity_tint", parseFloat(opacityTintSlider.value))
        mainWindowBackend.update_main_window_config("opacity_noise", parseFloat(opacityNoiseSlider.value))
        mainWindowBackend.update_main_window_config("background_color", mainWindowConfig.background_color || "#FFFFFF")
        mainWindowBackend.update_main_window_config("luminosity", parseFloat(luminositySlider.value))
        mainWindowBackend.update_main_window_config("enable_noise", enableNoiseSwitch.checked)

        mainWindowBackend.showMessage("成功", "所有配置已保存", "success")
    }

    // 重置为默认值
    function resetToDefaults() {
        // 重置所有控件为默认值
        radiusBlurSlider.value = 20
        backgroundOpacitySlider.value = 0.3
        opacityTintSlider.value = 0.15
        opacityNoiseSlider.value = 0.02
        luminositySlider.value = 0.1
        enableNoiseSwitch.checked = true

        // 重置配置
        var defaultConfig = {
            background_image: "",
            radius_blur: 20,
            background_opacity: 0.3,
            opacity_tint: 0.15,
            opacity_noise: 0.02,
            luminosity: 0.1,
            enable_noise: true,
            background_color: "#FFFFFF"
        }

        // 应用默认配置
        for (var key in defaultConfig) {
            mainWindowBackend.update_main_window_config(key, defaultConfig[key])
        }

        mainWindowBackend.showMessage("成功", "配置已重置为默认值", "success")
    }

    // 连接后端信号
    Connections {
        target: mainWindowBackend

        function onMain_window_config_updated(newConfig) {
            console.log("收到主窗口配置更新信号")
            mainWindowConfig = newConfig
            loadConfig()
            // 确保界面立即反映最新的配置
            if (backgroundImageLabel) {
                backgroundImageLabel.text = newConfig.background_image ? newConfig.background_image : "未选择图片"
            }
        }
    }
}