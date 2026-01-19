import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Qt5Compat.GraphicalEffects
import "components"

ApplicationWindow {
    id: window
    width: 1000
    height: 600
    minimumWidth: 800
    minimumHeight: 500
    visible: true
    title: "QuickLauncher - 主窗口"
    color: "transparent"  // 改为透明以支持背景效果
    flags: Qt.FramelessWindowHint | Qt.Window | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint

    // 主窗口配置属性
    property var mainWindowConfig: ({})

    // 毛玻璃效果背景层 - 放在最底层
    Item {
        id: glassBackground
        anchors.fill: parent

        // 主窗口背景图片 - 作为模糊效果的源
        Image {
            id: backgroundImage
            anchors.fill: parent
            source: mainWindowConfig.background_image
            fillMode: Image.PreserveAspectCrop
            visible: mainWindowConfig.background_image && mainWindowConfig.background_image !== ""
            clip: true
            asynchronous: true
            cache: true
            z: 0  // 确保背景图片在最底层
        }

        // 主窗口毛玻璃效果 - 应用到整个窗口，包含圆角效果
        GlassEffect {
            id: mainGlassEffect
            anchors.fill: parent
            sourceItem: backgroundImage.visible ? backgroundImage : parent  // 使用背景图片作为模糊源，如果没有则使用parent
            radiusBlur: (mainWindowConfig.radius_blur !== undefined && mainWindowConfig.radius_blur !== null) ? mainWindowConfig.radius_blur : 20
            opacityTint: (mainWindowConfig.background_opacity !== undefined && mainWindowConfig.background_opacity !== null) ? mainWindowConfig.background_opacity : 0.3  // 使用专门的background_opacity参数
            colorTint: mainWindowConfig.background_color ? Qt.rgba(
                parseInt(mainWindowConfig.background_color.substr(1, 2), 16) / 255.0,
                parseInt(mainWindowConfig.background_color.substr(3, 2), 16) / 255.0,
                parseInt(mainWindowConfig.background_color.substr(5, 2), 16) / 255.0,
                1.0
            ) : Qt.rgba(0.5, 0.5, 0.5, 1.0)
            opacityNoise: (mainWindowConfig.opacity_noise !== undefined && mainWindowConfig.opacity_noise !== null) ? mainWindowConfig.opacity_noise : 0.02
            luminosity: (mainWindowConfig.luminosity !== undefined && mainWindowConfig.luminosity !== null) ? mainWindowConfig.luminosity : 0.1
            radiusBg: 8  // 与主窗口一致的圆角
            enableNoise: (mainWindowConfig.enable_noise !== undefined && mainWindowConfig.enable_noise !== null) ? mainWindowConfig.enable_noise : true  // 启用噪声效果以增加磨砂质感
        }

        // 添加一个透明的圆角矩形覆盖在毛玻璃效果之上，以确保圆角边缘正确显示
        Rectangle {
            id: cornerMask
            anchors.fill: parent
            color: "transparent"
            radius: 8
            border.color: "transparent"  // 使用透明边框确保边缘不显示黑色
            border.width: 1
            clip: true
        }

        // 主窗口内容容器 - 保持不透明以确保内容清晰可见
        Item {
            id: mainContent
            anchors.fill: parent

            // 主布局 - 使用一个统一的圆角矩形来包含标题栏、导航栏和内容区域
            Rectangle {
                id: mainLayout
                anchors.fill: parent
                color: "transparent"  // 改为透明以支持背景效果
                radius: 8  // 统一的圆角设置，应用到整个界面的四个角
                clip: true  // 确保内容不会超出圆角边界

                // 整体布局容器 - 使用Column来垂直排列标题栏和主内容区
                Column {
                    anchors.fill: parent

                    // 自定义标题栏组件 - 只有顶部两个角是圆角
                    CornerClip {
                        id: titleBarClipContainer
                        width: parent.width
                        height: 30  // 确保标题栏有正确的高度
                        topLeft: true
                        topRight: true
                        bottomLeft: false
                        bottomRight: false
                        radius: 8
                        
                        TitleBar {
                            id: titleBar
                            width: parent.width
                            height: 30  // 确保标题栏有正确的高度
                            config: mainWindowConfig
                            titleText: "QuickLauncher - 主窗口"
                            window: window  // 传递窗口对象给标题栏
                            isMaximized: window.visibility === Window.Maximized

                            // 连接标题栏信号到主窗口逻辑
                            onMinimizeRequested: {
                                window.showMinimized();
                            }
                            onMaximizeRequested: {
                                if (window.visibility === Window.Maximized) {
                                    window.showNormal();
                                } else {
                                    window.showMaximized();
                                }
                            }
                            onCloseRequested: {
                                // 使用关闭事件而不是直接退出，这样可以触发托盘功能
                                window.close();
                            }
                        }
                    }

                    // 主内容区域 - 包含导航栏和右侧内容区域
                    Item {
                        id: contentArea
                        width: parent.width
                        height: parent.height - titleBar.height  // 剩余高度

                        Row {
                            anchors.fill: parent

                            // 左侧导航栏组件 - 只有左下角是圆角
                            CornerClip {
                                id: sideBarClipContainer
                                width: 200
                                height: parent.height
                                topLeft: false
                                topRight: false
                                bottomLeft: true
                                bottomRight: false
                                radius: 8

                                SideBar {
                                    id: sideBar
                                    width: 200
                                    height: parent.height
                                    mainWindowConfig: mainWindowConfig
                                    contentLoader: contentLoader
                                    currentSource: contentLoader.source
                                    appCount: 0  // 这个值将在主窗口中更新

                                    // 连接导航栏按钮点击信号
                                    onAppManagementClicked: {
                                        console.log("加载应用管理页面")
                                        contentLoader.source = ""
                                        contentLoader.source = "components/AppManagement.qml"
                                    }
                                    onQuickWindowManagementClicked: {
                                        console.log("加载快捷窗口设置页面")
                                        contentLoader.source = ""
                                        contentLoader.source = "components/QuickWindowManagement.qml"
                                    }
                                    onMainWindowManagementClicked: {
                                        console.log("加载主窗口设置页面")
                                        contentLoader.source = ""
                                        contentLoader.source = "components/MainWindowManagement.qml"
                                    }
                                    onAboutClicked: {
                                        console.log("加载关于页面")
                                        contentLoader.source = ""
                                        contentLoader.source = "components/About.qml"
                                    }
                                }
                            }

                            // 右侧内容区域 - 只有右下角是圆角
                            CornerClip {
                                id: rightContentArea
                                width: parent.width - sideBar.width  // 剩余宽度
                                height: parent.height
                                topLeft: false
                                topRight: false
                                bottomLeft: false
                                bottomRight: true
                                radius: 8

                                // 内容区域内容容器
                                Item {
                                    id: contentForeground
                                    anchors.fill: parent
                                    anchors.margins: 1  // 添加小边距以确保内容区域与其他组件间距一致
                                    clip: true  // 确保内容不会超出边界
                                    z: 2  // 确保内容在毛玻璃效果之上
                                    
                                    Loader {
                                        id: contentLoader
                                        anchors.fill: parent
                                        anchors.margins: 10  // 添加与其他组件相同的边距

                                        onLoaded: {
                                            console.log("组件加载成功:", source)
                                        }

                                        onStatusChanged: {
                                            if (status === Loader.Error) {
                                                console.log("组件加载错误:", source)
                                                errorText.text = "加载组件失败: " + source
                                                errorText.visible = true
                                            } else {
                                                errorText.visible = false
                                            }
                                        }

                                    }

                                    // 错误信息
                                    Text {
                                        id: errorText
                                        anchors.centerIn: parent
                                        color: "#F43336"
                                        font.pixelSize: 16
                                        visible: false
                                    }
                                }


                            }
                        }
                    }
                }
            }

            // 连接后端信号 - 使用正确的信号名称
            Connections {
                target: mainWindowBackend

                // 注意：信号名称必须与Python后端完全匹配（下划线格式）
                function onShow_message(title, message, type) {
                    console.log("收到显示消息信号:", title, message, type)
                    // 可以在这里添加消息框显示逻辑
                }

                function onOperation_status(operation, message) {
                    console.log("收到操作状态信号:", operation, message)
                    if (sideBar && sideBar.statusText) {
                        sideBar.statusText.text = message
                    }
                    // 3秒后恢复默认状态
                    operationStatusTimer.restart()
                }

                function onApp_list_updated(apps) {
                    console.log("收到应用列表更新信号，数量:", apps.length)
                    if (sideBar && sideBar.appCountText) {
                        sideBar.appCountText.text = "应用: " + apps.length
                    }
                        sideBar.appCount = apps.length  // 更新appCount属性
                }
                
                function onMain_window_config_updated(newConfig) {
                    console.log("【QML DEBUG】收到主窗口配置更新信号")
                    console.log("【QML DEBUG】新的配置: " + JSON.stringify(newConfig))
                    mainWindowConfig = newConfig
                    updateMainWindowEffects()
                    
                    // 确保界面立即更新 - 更新所有毛玻璃效果组件
                    if (newConfig.radius_blur !== undefined && newConfig.radius_blur !== null) {
                        mainGlassEffect.radiusBlur = newConfig.radius_blur
                        console.log("【QML DEBUG】更新模糊半径: " + newConfig.radius_blur)
                    }
                    // 使用专门的background_opacity参数来控制毛玻璃效果透明度，而不是混用opacity参数
                    if (newConfig.background_opacity !== undefined && newConfig.background_opacity !== null) {
                        mainGlassEffect.opacityTint = newConfig.background_opacity
                        console.log("【QML DEBUG】更新背景透明度: " + newConfig.background_opacity)
                    } else if (newConfig.opacity !== undefined && newConfig.opacity !== null) {
                        // 向后兼容：如果未设置background_opacity，则使用opacity作为背景透明度
                        mainGlassEffect.opacityTint = newConfig.opacity
                        console.log("【QML DEBUG】更新透明度 (向后兼容): " + newConfig.opacity)
                    }
                    if (newConfig.opacity_noise !== undefined && newConfig.opacity_noise !== null) {
                        mainGlassEffect.opacityNoise = newConfig.opacity_noise
                        console.log("【QML DEBUG】更新噪声透明度: " + newConfig.opacity_noise)
                    }
                    if (newConfig.background_color) {
                        var colorTint = Qt.rgba(
                            parseInt(newConfig.background_color.substr(1, 2), 16) / 255.0,
                            parseInt(newConfig.background_color.substr(3, 2), 16) / 255.0,
                            parseInt(newConfig.background_color.substr(5, 2), 16) / 255.0,
                            1.0
                        )
                        mainGlassEffect.colorTint = colorTint
                        console.log("【QML DEBUG】更新背景颜色: " + newConfig.background_color)
                    }
                    
                    // 如果背景图片路径发生变化，需要重新加载图片
                    if (newConfig.background_image !== undefined) {
                        console.log("【QML DEBUG】更新背景图片路径: " + newConfig.background_image)
                        // 配置中的路径是相对路径，需要正确处理为file://URL
                        var imagePath = newConfig.background_image;
                        if (imagePath && imagePath !== "") {
                            // 确保路径格式正确 - 如果不是file://协议，则添加协议前缀
                            if (imagePath.startsWith("file://")) {
                                backgroundImage.source = imagePath;
                            } else {
                                // 使用相对路径，转换为绝对路径
                                backgroundImage.source = "file://" + imagePath;
                            }
                        } else {
                            backgroundImage.source = "";
                        }
                        backgroundImage.visible = (imagePath && imagePath !== "");
                        console.log("【QML DEBUG】背景图片可见性: " + backgroundImage.visible)
                    }
                }
            }

            // 操作状态定时器
            Timer {
                id: operationStatusTimer
                interval: 3000
                onTriggered: {
                    if (sideBar && sideBar.statusText) {
                        sideBar.statusText.text = "就绪"
                    }
                }
            }

            // 初始化
            Component.onCompleted: {
                console.log("主窗口初始化完成")

                // 获取主窗口配置
                mainWindowConfig = mainWindowBackend.get_main_window_config()
                console.log("主窗口配置:", JSON.stringify(mainWindowConfig))

                // 获取初始应用列表
                var apps = mainWindowBackend.get_applications()
                if (sideBar && sideBar.appCountText) {
                    sideBar.appCountText.text = "应用: " + apps.length
                }
                sideBar.appCount = apps.length
                
                // 更新主窗口效果
                updateMainWindowEffects()
                
                // 设置背景图片
                if (mainWindowConfig.background_image && mainWindowConfig.background_image !== "") {
                    var imagePath = mainWindowConfig.background_image;
                    // 确保路径格式正确 - 如果不是file://协议，则添加协议前缀
                    if (imagePath.startsWith("file://")) {
                        backgroundImage.source = imagePath;
                    } else {
                        backgroundImage.source = "file://" + imagePath;
                    }
                    backgroundImage.visible = true;
                } else {
                    backgroundImage.source = "";
                    backgroundImage.visible = false;
                }
            }
            
            // 更新主窗口效果
            function updateMainWindowEffects() {
                // 确保配置值有效
                if (mainWindowConfig.background_opacity === undefined || mainWindowConfig.background_opacity === null) {
                    mainWindowConfig.background_opacity = 0.3  // 背景毛玻璃透明度，默认值为0.3
                }
                if (mainWindowConfig.background_color === undefined || mainWindowConfig.background_color === null) {
                    mainWindowConfig.background_color = "#FFFFFF"
                }
                
                // 更新背景图片
                if (mainWindowConfig.background_image && mainWindowConfig.background_image !== "") {
                    var imagePath = mainWindowConfig.background_image;
                    // 确保路径格式正确 - 如果不是file://协议，则添加协议前缀
                    if (imagePath.startsWith("file://")) {
                        backgroundImage.source = imagePath;
                    } else {
                        backgroundImage.source = "file://" + imagePath;
                    }
                    backgroundImage.visible = true;
                } else {
                    backgroundImage.source = "";
                    backgroundImage.visible = false;
                }
                
                // 创建一个更新函数来避免重复代码
                function updateGlassEffect(effect, config) {
                    if (config.radius_blur !== undefined && config.radius_blur !== null) {
                        effect.radiusBlur = config.radius_blur;
                    }
                    // 使用专门的background_opacity参数来控制毛玻璃效果透明度，而不是混用opacity参数
                    if (config.background_opacity !== undefined && config.background_opacity !== null) {
                        effect.opacityTint = config.background_opacity;
                    } else if (config.opacity !== undefined && config.opacity !== null) {
                        // 向后兼容：如果未设置background_opacity，则使用opacity作为背景透明度
                        effect.opacityTint = config.opacity;
                    }
                    if (config.opacity_noise !== undefined && config.opacity_noise !== null) {
                        effect.opacityNoise = config.opacity_noise;
                    }
                    if (config.background_color) {
                        var colorTint = Qt.rgba(
                            parseInt(config.background_color.substr(1, 2), 16) / 255.0,
                            parseInt(config.background_color.substr(3, 2), 16) / 255.0,
                            parseInt(config.background_color.substr(5, 2), 16) / 255.0,
                            1.0
                        );
                        effect.colorTint = colorTint;
                    }
                    // 注意：GlassEffect组件中没有background_noise属性，这里不需要处理

                }
                
                // 更新所有毛玻璃效果参数 - 现在包含内容区域的毛玻璃效果
                updateGlassEffect(mainGlassEffect, mainWindowConfig);
            }
        }
    }

    // 窗口状态变化时更新标题栏的isMaximized属性
    onVisibilityChanged: {
        // 触发标题栏的isMaximized属性更新
        titleBar.isMaximized = window.visibility === Window.Maximized
    }

    // 窗口关闭事件处理 - 使用Connections组件
    Connections {
        target: window

        function onClosing(close) {
            // 最小化到托盘而不是关闭
            close.accepted = false
            window.hide()

            // 检查trayManager是否存在（在预览模式下可能不存在）
            if (typeof trayManager !== 'undefined' && trayManager !== null) {
                trayManager.showMessage("QuickLauncher", "应用程序已最小化到系统托盘")
            } else {
                console.log("预览模式：trayManager未定义")
            }
        }
    }

}