import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects


ApplicationWindow {
    id: quickWindow
    width: 60  // 初始宽度，将由updateWindowSize动态调整
    height: 100  // 初始高度，将由updateWindowSize动态调整
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint
    color: "transparent"
    visible: true
    // 注意：不再直接设置窗口透明度，而是通过背景层控制

    // 配置属性
    property var config: ({})
    property var apps: []

    property int currentAppIndex: -1
    property bool labelsVisible: false
    
    // 透明度属性 - 确保圆角窗口的整体透明度正确显示
    property real windowOpacity: 1.0
    
    // 辅助函数：从十六进制颜色字符串中提取颜色组件
    function getColorComponent(colorStr, start, length) {
        if (colorStr && colorStr.length >= start + length) {
            var sub = colorStr.substr(start, length);
            return parseInt(sub, 16);
        }
        return 0;
    }

    // 毛玻璃背景 - 使用GlassEffect组件实现真正的磨砂玻璃效果
    Item {
        id: backgroundItem
        anchors.fill: parent
        opacity: windowOpacity  // 应用透明度到背景层，而不是整个窗口
        
        // 毛玻璃效果实现
        GlassEffect {
            id: glassEffect
            anchors.fill: parent
            sourceItem: parent
            radiusBlur: (config.radius_blur !== undefined && config.radius_blur !== null) ? config.radius_blur : 16
            opacityTint: (config.opacity_tint !== undefined && config.opacity_tint !== null) ? config.opacity_tint : 0.15
            colorTint: config.background_color ? Qt.rgba(
                parseInt(config.background_color.substr(1, 2), 16) / 255.0,
                parseInt(config.background_color.substr(3, 2), 16) / 255.0,
                parseInt(config.background_color.substr(5, 2), 16) / 255.0,
                1.0
            ) : Qt.rgba(0.5, 0.5, 0.5, 1.0)
            opacityNoise: (config.opacity_noise !== undefined && config.opacity_noise !== null) ? config.opacity_noise : 0.02
            luminosity: 0.1
            radiusBg: 10
            enableNoise: false  // 快捷窗口默认不启用噪声效果
        }
        
        // 边框
        Rectangle {
            id: borderRect
            anchors.fill: parent
            color: "transparent"
            radius: 10
            border.color: Qt.darker(config.background_color || "#FFFFFF", 1.2)
            border.width: 1
            clip: true  // 确保内容被圆角裁剪
        }
    }

    // 添加阴影效果
    DropShadow {
        anchors.fill: backgroundItem
        horizontalOffset: 0
        verticalOffset: 2
        radius: 10
        samples: 17
        color: "#40000000"
        source: backgroundItem
        transparentBorder: true
    }

    // 应用图标网格 - 使用GridLayout实现多行多列网格布局
    Item {
        id: appGridContainer
        anchors.centerIn: parent
        width: Math.min(parent.width - 40, maxGridWidth)  // 最大宽度不超过窗口宽度减去边距
        height: Math.min(parent.height - 40, maxGridHeight)  // 最大高度不超过窗口高度减去边距
        z: 2  // 确保内容在毛玻璃效果之上
        
        // 计算最大网格尺寸
        property int maxGridWidth: {
            var layoutInfo = quickWindowBackend ? quickWindowBackend.get_grid_layout_info() : {};
            var cols = layoutInfo.cols || (config.cols || 5);
            var iconSize = config.icon_size || 48;
            var spacing = config.icon_spacing || 10;
            // 宽度 = 左边距+图标+（间隙+图标）*(m-1)+右边距
            return spacing + iconSize + (spacing + iconSize) * (cols - 1) + spacing;
        }
        property int maxGridHeight: {
            var layoutInfo = quickWindowBackend ? quickWindowBackend.get_grid_layout_info() : {};
            var rows = layoutInfo.rows || 1;
            var iconSize = config.icon_size || 48;
            var labelHeight = labelsVisible ? 20 : 0;
            var spacing = config.icon_spacing || 10;
            // 高度 = 上边距+图标+应用名+（间隙+图标+应用名）*(n-1)+下边距
            return spacing + (iconSize + labelHeight) + (spacing + (iconSize + labelHeight)) * (rows - 1) + spacing;
        }
        
        // GridLayout来实现网格布局
        Item {
            id: appLayoutContainer
            anchors.centerIn: parent
            width: {
                var layoutInfo = quickWindowBackend ? quickWindowBackend.get_grid_layout_info() : {};
                var cols = layoutInfo.cols || (config.cols || 5);
                var iconSize = config.icon_size || 48;
                var spacing = 5; // 间隙固定为5
                var margin = config.icon_spacing || 10; // 边距
                // 宽度 = 左边距+图标+（间隙+图标）*(m-1)+右边距
                return margin + iconSize + (spacing + iconSize) * (cols - 1) + margin;
            }
            height: {
                var layoutInfo = quickWindowBackend ? quickWindowBackend.get_grid_layout_info() : {};
                var rows = layoutInfo.rows || 1;
                var iconSize = config.icon_size || 48;
                var labelHeight = labelsVisible ? 20 : 0;
                var spacing = 5; // 间隙固定为5
                var margin = config.icon_spacing || 10; // 边距
                // 高度 = 上边距+图标+应用名+（间隙+图标+应用名）*(n-1)+下边距
                return margin + (iconSize + labelHeight) + (spacing + (iconSize + labelHeight)) * (rows - 1) + margin;
            }
            
            // 动态创建应用图标项
            Repeater {
                id: appRepeater
                model: {
                    if (quickWindowBackend) {
                        var allApps = quickWindowBackend.get_apps();
                        var appOrder = config.app_order || [];
                        // 根据配置的app_order排序并限制数量
                        var orderedApps = [];
                        for (var i = 0; i < appOrder.length; i++) {
                            for (var j = 0; j < allApps.length; j++) {
                                if (allApps[j].id === appOrder[i]) {
                                    orderedApps.push(allApps[j]);
                                    break;
                                }
                            }
                        }
                        
                        // 获取配置的行数和列数
                        var rows = config.rows || 1;
                        var cols = config.cols || 5;
                        var maxApps = rows * cols;
                        
                        // 应用数量限制：只显示前n×m个应用
                        if (orderedApps.length > maxApps) {
                            console.log("应用数量超出限制，只显示前", maxApps, "个应用")
                            orderedApps = orderedApps.slice(0, maxApps);
                        }
                        
                        return orderedApps;
                    } else if (mainWindowBackend) {
                        var allApps = mainWindowBackend.get_applications();
                        var appOrder = config.app_order || [];
                        // 根据配置的app_order排序并限制数量
                        var orderedApps = [];
                        for (var i = 0; i < appOrder.length; i++) {
                            for (var j = 0; j < allApps.length; j++) {
                                if (allApps[j].id === appOrder[i]) {
                                    orderedApps.push(allApps[j]);
                                    break;
                                }
                            }
                        }
                        
                        // 获取配置的行数和列数
                        var rows = config.rows || 1;
                        var cols = config.cols || 5;
                        var maxApps = rows * cols;
                        
                        // 应用数量限制：只显示前n×m个应用
                        if (orderedApps.length > maxApps) {
                            console.log("应用数量超出限制，只显示前", maxApps, "个应用")
                            orderedApps = orderedApps.slice(0, maxApps);
                        }
                        
                        return orderedApps;
                    }
                    return [];
                }
                
                Item {
                    id: gridItem
                    width: config.icon_size || 48
                    height: (config.icon_size || 48) + (labelsVisible ? 20 : 0)
                    
                    // 获取网格布局信息
                    property var layoutInfo: quickWindowBackend ? quickWindowBackend.get_grid_layout_info() : {}
                    
                    // 从布局信息中获取当前应用的行和列
                    property var appPosition: (layoutInfo.app_positions && index < layoutInfo.app_positions.length) ? 
                                             layoutInfo.app_positions[index] : {row: 0, col: 0};
                    property int currentRow: appPosition.row || 0;
                    property int currentCol: appPosition.col || 0;
                    
                    // 确定当前项是否在特殊行（顶部位置的最后一行或底部位置的第一行）
                    property bool isSpecialRow: {
                        if (layoutInfo.special_row_info && Object.keys(layoutInfo.special_row_info).length > 0) {
                            if (config.position === "top_center") {
                                // 顶部位置：最后一行需要居中
                                return currentRow === layoutInfo.special_row_info.special_row;
                            } else if (config.position === "bottom_center") {
                                // 底部位置：第一行需要居中
                                return currentRow === layoutInfo.special_row_info.special_row;
                            }
                        }
                        return false;
                    }
                    
                    // 计算特殊行的居中偏移
                    property real centerOffset: {
                        if (!isSpecialRow || !layoutInfo.special_row_info) {
                            return 0;  // 不是特殊行，无需偏移
                        }
                        
                        var itemsInSpecialRow = layoutInfo.special_row_info.apps_in_special_row || 0;
                        var totalCells = layoutInfo.special_row_info.items_per_row || (config.cols || 5);
                        var occupiedCells = itemsInSpecialRow;
                        var cellWidth = (config.icon_size || 48) + 5; // 图标大小+间隙
                        var offset = (totalCells - occupiedCells) * cellWidth / 2;
                        return offset;
                    }
                    
                    // 计算位置
                    x: {
                        var iconSize = config.icon_size || 48;
                        var spacing = 5; // 间隙固定为5
                        var margin = config.icon_spacing || 10; // 边距
                        
                        if (isSpecialRow) {
                            // 特殊行需要居中偏移
                            var baseX = margin + (currentCol * (iconSize + spacing)) + centerOffset;
                            return baseX;
                        } else {
                            // 普通行正常计算位置
                            return margin + (currentCol * (iconSize + spacing));
                        }
                    }
                    y: {
                        var iconSize = config.icon_size || 48;
                        var labelHeight = labelsVisible ? 20 : 0;
                        var spacing = 5; // 间隙固定为5
                        var margin = config.icon_spacing || 10; // 边距
                        
                        // 计算行位置
                        return margin + (currentRow * (iconSize + labelHeight + spacing));
                    }
                    
                    // 应用图标容器
                    Rectangle {
                        id: iconContainer
                        width: config.icon_size || 48
                        height: config.icon_size || 48
                        x: 0
                        y: 0
                        color: "#00000000"  // 完全透明，但保持容器结构
                        radius: 8
                        
                        // 应用图标
                        Image {
                            id: iconImage
                            anchors.centerIn: parent
                            width: parent.width * 0.9
                            height: parent.width * 0.9
                            source: modelData.icon_path ? modelData.icon_path : ("image://icon/" + encodeURIComponent(modelData.path))
                            fillMode: Image.PreserveAspectFit
                            sourceSize.width: config.icon_size || 48
                            sourceSize.height: config.icon_size || 48

                            // 悬停放大效果
                            scale: 1.0
                            Behavior on scale {
                                NumberAnimation {
                                    duration: 200
                                    easing.type: Easing.OutCubic
                                }
                            }
                        }

                        // 鼠标区域
                        MouseArea {
                            id: iconMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor

                            onEntered: {
                                // 确保配置已加载并应用悬停放大效果
                                if (config.hover_scale !== undefined && config.hover_scale !== null) {
                                    iconImage.scale = config.hover_scale
                                } else {
                                    iconImage.scale = 1.2  // 默认放大比例
                                }
                                currentAppIndex = index
                            }

                            onExited: {
                                iconImage.scale = 1.0
                                currentAppIndex = -1
                            }

                            onDoubleClicked: {
                                launchApp(index)
                            }
                        }
                    }

                    // 应用名称
                    Text {
                        id: appName
                        anchors {
                            top: iconContainer.bottom
                            horizontalCenter: iconContainer.horizontalCenter
                        }
                        text: modelData.name
                        color: "white"
                        font.pixelSize: 10
                        font.bold: true
                        visible: labelsVisible
                        elide: Text.ElideRight
                        width: parent.width - 10
                        horizontalAlignment: Text.AlignHCenter
                        anchors.topMargin: 5

                        // 文字阴影
                        layer.enabled: true
                        layer.effect: DropShadow {
                            transparentBorder: true
                            horizontalOffset: 0
                            verticalOffset: 1
                            radius: 2
                            samples: 5
                            color: "#80000000"
                        }
                    }
                }
            }
        }
    }

    // 如果没有应用
    Rectangle {
        anchors.centerIn: parent
        width: 300
        height: 100
        color: "transparent"
        visible: (config.app_order && config.app_order.length) === 0
        z: 2  // 确保内容在毛玻璃效果之上

        Column {
            anchors.centerIn: parent
            spacing: 10

            Text {
                text: ""
                color: "#888"
                font.pixelSize: 32
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text {
                text: "暂无应用"
                color: "#888"
                font.pixelSize: 14
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text {
                text: "请在主窗口中添加应用"
                color: "#666"
                font.pixelSize: 12
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }

    // 鼠标区域（用于双击切换显示）
    MouseArea {
        id: windowMouseArea
        anchors.fill: parent
        enabled: quickWindow.visible
        propagateComposedEvents: true
        z: 3  // 确保鼠标区域在所有内容之上
    }

    // 初始化应用列表
    Component.onCompleted: {
        console.log("QuickWindow初始化完成")

        // 加载配置
        loadConfig()

        // 加载应用列表
        loadApps()

        // 根据配置的auto_start参数设置初始可见性
        if (config.auto_start) {
            quickWindow.visible = true
        } else {
            quickWindow.visible = false
        }

        // 定位窗口
        positionWindow()
        
        // 确保背景透明度和颜色正确应用
        // 使用专门的background_opacity参数来控制毛玻璃效果透明度，而不是混用opacity参数
        if (config.background_opacity !== undefined && config.background_opacity !== null) {
            glassEffect.opacityTint = config.background_opacity
        } else if (config.opacity !== undefined && config.opacity !== null) {
            // 向后兼容：如果未设置background_opacity，则使用opacity作为背景透明度
            glassEffect.opacityTint = config.opacity
        }
        
        // 设置窗口整体透明度 - 根据规范，将opacity属性直接应用于窗口根元素
        if (config.opacity !== undefined && config.opacity !== null) {
            quickWindow.windowOpacity = config.opacity
        }
        
        if (config.background_color !== undefined && config.background_color !== null) {
            glassEffect.colorTint = Qt.rgba(
                parseInt(config.background_color.substr(1, 2), 16) / 255.0,
                parseInt(config.background_color.substr(3, 2), 16) / 255.0,
                parseInt(config.background_color.substr(5, 2), 16) / 255.0,
                1.0
            )
            borderRect.border.color = Qt.darker(config.background_color, 1.2)
        }
    }

    // 加载配置
    function loadConfig() {
        if (quickWindowBackend) {
            config = quickWindowBackend.get_config()
        } else if (mainWindowBackend) {
            config = mainWindowBackend.get_quick_window_config()
        }

        console.log("快捷窗口配置:", JSON.stringify(config))

        // 确保配置值有效
        if (config.opacity === undefined || config.opacity === null) {
            config.opacity = 0.9  // 窗口整体透明度，默认值为0.9
        }
        if (config.hover_scale === undefined || config.hover_scale === null) {
            config.hover_scale = 1.5
        }
        if (config.background_color === undefined || config.background_color === null) {
            config.background_color = "#FFFFFF"
        }
        if (config.show_labels === undefined || config.show_labels === null) {
            config.show_labels = false  // 默认不显示标签
        }
        if (config.opacity_noise === undefined || config.opacity_noise === null) {
            config.opacity_noise = 0.01
        }
        if (config.opacity_tint === undefined || config.opacity_tint === null) {
            config.opacity_tint = 0.15
        }
        if (config.radius_blur === undefined || config.radius_blur === null) {
            config.radius_blur = 20
        }
        if (config.background_opacity === undefined || config.background_opacity === null) {
            config.background_opacity = 0.3  // 背景毛玻璃透明度，默认值为0.3
        }
        if (config.rows === undefined || config.rows === null) {
            config.rows = 1  // 默认行数为1
        }
        if (config.cols === undefined || config.cols === null) {
            config.cols = 5  // 默认列数为5
        }
        if (config.icon_spacing === undefined || config.icon_spacing === null) {
            config.icon_spacing = 10  // 默认图标间距为10
        }

        // 更新界面
        // 根据配置中的show_labels设置来决定是否显示标签
        labelsVisible = config.show_labels === true
        
        // 立即更新背景颜色和透明度
        if (config.background_color) {
            glassEffect.colorTint = Qt.rgba(
                parseInt(config.background_color.substr(1, 2), 16) / 255.0,
                parseInt(config.background_color.substr(3, 2), 16) / 255.0,
                parseInt(config.background_color.substr(5, 2), 16) / 255.0,
                1.0
            )
        }
        // 使用专门的background_opacity参数来控制毛玻璃效果透明度，而不是混用opacity参数
        if (config.background_opacity !== undefined && config.background_opacity !== null) {
            glassEffect.opacityTint = config.background_opacity
        } else if (config.opacity !== undefined && config.opacity !== null) {
            // 向后兼容：如果未设置background_opacity，则使用opacity作为背景透明度
            glassEffect.opacityTint = config.opacity
        }
        
        // 立即更新边框颜色
        borderRect.border.color = Qt.darker(config.background_color, 1.2)

        // 更新窗口大小
        updateWindowSize()

        // 更新窗口位置
        if (config.position) {
            positionWindow()
        }

        // 重新加载应用顺序
        loadApps()
    }

    // 加载应用列表
    function loadApps() {
        if (quickWindowBackend) {
            apps = quickWindowBackend.get_apps()
        } else if (mainWindowBackend) {
            apps = mainWindowBackend.get_applications()
        }

        console.log("快捷窗口应用数量:", apps.length)

        // 只显示配置中指定的快捷应用
        var orderedApps = []
        var appOrder = config.app_order || []

        // 按配置中的顺序添加应用
        for (var i = 0; i < appOrder.length; i++) {
            for (var j = 0; j < apps.length; j++) {
                if (apps[j].id === appOrder[i]) {
                    orderedApps.push(apps[j])
                    break
                }
            }
        }
        
        // 获取配置的行数和列数
        var rows = config.rows || 1
        var cols = config.cols || 5
        var maxApps = rows * cols
        
        // 应用数量限制：只显示前n×m个应用
        if (orderedApps.length > maxApps) {
            console.log("应用数量超出限制，只显示前", maxApps, "个应用")
            orderedApps = orderedApps.slice(0, maxApps)
        }

        // 更新窗口大小
        updateWindowSize()
    }

    // 更新窗口大小
    function updateWindowSize() {
        // 从后端获取网格布局信息
        if (quickWindowBackend) {
            var layoutInfo = quickWindowBackend.get_grid_layout_info()
            
            if (layoutInfo && layoutInfo.width && layoutInfo.height) {
                quickWindow.width = layoutInfo.width
                quickWindow.height = layoutInfo.height
                console.log("根据后端布局信息更新窗口尺寸:", layoutInfo.width, "x", layoutInfo.height)
            } else {
                // 备用计算方式
                var iconSize = config.icon_size || 48
                var iconSpacing = config.icon_spacing || 10
                var labelHeight = labelsVisible ? 20 : 0
                
                // 获取配置的行数和列数
                var rows = config.rows || 1
                var cols = config.cols || 5
                
                // 计算实际显示的应用数量（不超过配置的网格大小）
                var maxApps = rows * cols
                var appCount = Math.min((config.app_order || []).length, maxApps)
                console.log("快捷应用数量:", appCount, "最大应用数量:", maxApps, "配置行数:", rows, "配置列数:", cols)
                
                // 根据布局算法计算实际行数
                var actualRows = Math.ceil(appCount / cols);
                console.log("实际行数:", actualRows)
                
                // 根据项目规范，窗口尺寸计算：
                // 宽度 = 左边距+图标+（间隙+图标）*(m-1)+右边距
                // 高度 = 上边距+图标+应用名+（间隙+图标+应用名）*(n-1)+下边距
                // 边距长度10，间隙5
                if (appCount === 0) {
                    quickWindow.width = 200
                    quickWindow.height = 100
                } else {
                    // 根据实际显示的列数计算宽度，而不是总列数
                    var actualCols = Math.min(cols, appCount); // 实际显示的列数
                    if (appCount < cols && actualRows === 1) {
                        actualCols = appCount; // 单行情况下，实际列数是应用数量
                    }
                    
                    // 宽度计算：icon_spacing + icon_size + (5 + icon_size) * (actualCols - 1) + icon_spacing
                    var margin = iconSpacing;  // 边距
                    var gap = 5;  // 间隙
                    var windowWidth = margin + iconSize + (gap + iconSize) * (actualCols - 1) + margin;
                    // 高度计算：margin + (icon_size + labelHeight) + (gap + (icon_size + labelHeight)) * (actualRows - 1) + margin
                    var windowHeight = margin + (iconSize + labelHeight) + (gap + (icon_size + labelHeight)) * (actualRows - 1) + margin;
                    console.log("窗口尺寸:", windowWidth, "x", windowHeight, "实际行数:", actualRows, "实际列数:", actualCols)
                    
                    quickWindow.width = windowWidth
                    quickWindow.height = windowHeight
                }
            }
        } else {
            // 备用计算方式
            var iconSize = config.icon_size || 48
            var iconSpacing = config.icon_spacing || 10
            var labelHeight = labelsVisible ? 20 : 0
            
            // 获取配置的行数和列数
            var rows = config.rows || 1
            var cols = config.cols || 5
            
            // 计算实际显示的应用数量（不超过配置的网格大小）
            var maxApps = rows * cols
            var appCount = Math.min((config.app_order || []).length, maxApps)
            console.log("快捷应用数量:", appCount, "最大应用数量:", maxApps, "配置行数:", rows, "配置列数:", cols)
            
            // 计算实际行数
            var actualRows = Math.ceil(appCount / cols);
            if (appCount === 0) {
                actualRows = 0;
            }
            console.log("实际行数:", actualRows)
            
            if (appCount === 0) {
                quickWindow.width = 200
                quickWindow.height = 100
            } else {
                // 根据实际显示的列数计算宽度，而不是总列数
                var actualCols = Math.min(cols, appCount); // 实际显示的列数
                if (appCount < cols && actualRows === 1) {
                    actualCols = appCount; // 单行情况下，实际列数是应用数量
                }
                
                // 宽度计算：icon_spacing + icon_size + (5 + icon_size) * (actualCols - 1) + icon_spacing
                var margin = iconSpacing;  // 边距
                var gap = 5;  // 间隙
                var windowWidth = margin + iconSize + (gap + iconSize) * (actualCols - 1) + margin;
                // 高度计算：margin + (icon_size + labelHeight) + (gap + (icon_size + labelHeight)) * (actualRows - 1) + margin
                var windowHeight = margin + (iconSize + labelHeight) + (gap + (icon_size + labelHeight)) * (actualRows - 1) + margin;
                console.log("窗口尺寸:", windowWidth, "x", windowHeight, "实际行数:", actualRows, "实际列数:", actualCols)
                
                quickWindow.width = windowWidth
                quickWindow.height = windowHeight
            }
        }

        // 重新定位窗口
        positionWindow()
    }

    // 定位窗口
    function positionWindow() {
        if (quickWindowBackend) {
            var geometry = quickWindowBackend.get_window_geometry()
            quickWindow.x = geometry.x
            quickWindow.y = geometry.y
            quickWindow.width = geometry.width
            quickWindow.height = geometry.height
        } else {
            // 默认位置：屏幕右下角
            var screen = Qt.application.screens[0]
            quickWindow.x = screen.width / 2 - quickWindow.width / 2  // 屏幕水平居中
            quickWindow.y = 10  // 距离顶部10像素（默认顶部居中）
        }
        
        // 确保窗口居中于屏幕顶部或底部
        var screen = Qt.application.screens[0]
        if (config.position === "top_center") {
            quickWindow.x = screen.width / 2 - quickWindow.width / 2  // 水平居中
            quickWindow.y = 10  // 距离顶部10像素
        } else if (config.position === "bottom_center") {
            quickWindow.x = screen.width / 2 - quickWindow.width / 2  // 水平居中
            quickWindow.y = screen.height - quickWindow.height - 10  // 距离底部10像素
        }
    }

    // 启动应用
    function launchApp(index) {
        var appOrder = config.app_order || [];
        if (index >= 0 && index < appOrder.length) {
            var appId = appOrder[index];
            
            if (quickWindowBackend) {
                // 直接使用应用ID启动，而不是使用索引
                quickWindowBackend.launch_app_by_id(appId)
            } else if (mainWindowBackend) {
                mainWindowBackend.launch_application(appId)
            }

            // 可选：启动后隐藏窗口
            // quickWindow.hide()
        }
    }

    // 显示窗口
    function showWindow() {
        quickWindow.visible = true
        quickWindow.raise()
        quickWindow.requestActivate()
    }

    // 隐藏窗口
    function hideWindow() {
        quickWindow.visible = false
    }

    // 切换窗口显示状态
    function toggleWindowVisibility() {
        if (quickWindow.visible) {
            hideWindow()
        } else {
            showWindow()
        }
    }

    // 连接后端信号
    Connections {
        target: quickWindowBackend ? quickWindowBackend : null

        function onConfig_updated(newConfig) {
            console.log("收到配置更新信号")
            config = newConfig

            // 确保配置值有效
            if (config.opacity === undefined || config.opacity === null) {
                config.opacity = 0.9  // 窗口整体透明度，默认值为0.9
            }
            if (config.hover_scale === undefined || config.hover_scale === null) {
                config.hover_scale = 1.5
            }
            if (config.background_color === undefined || config.background_color === null) {
                config.background_color = "#FFFFFF"
            }
            if (config.background_opacity === undefined || config.background_opacity === null) {
                config.background_opacity = 0.3  // 背景毛玻璃透明度，默认值为0.3
            }
            if (config.rows === undefined || config.rows === null) {
                config.rows = 1  // 默认行数为1
            }
            if (config.cols === undefined || config.cols === null) {
                config.cols = 5  // 默认列数为5
            }
            if (config.icon_spacing === undefined || config.icon_spacing === null) {
                config.icon_spacing = 10  // 默认图标间距为10
            }

            // 更新界面
            // 根据配置中的show_labels设置来决定是否显示标签
            labelsVisible = config.show_labels === true
            
            // 立即更新背景颜色和透明度
            if (config.background_color) {
                glassEffect.colorTint = Qt.rgba(
                    parseInt(config.background_color.substr(1, 2), 16) / 255.0,
                    parseInt(config.background_color.substr(3, 2), 16) / 255.0,
                    parseInt(config.background_color.substr(5, 2), 16) / 255.0,
                    1.0
                )
            }
            // 使用专门的background_opacity参数来控制毛玻璃效果透明度，而不是混用opacity参数
            if (config.background_opacity !== undefined && config.background_opacity !== null) {
                glassEffect.opacityTint = config.background_opacity
            } else if (config.opacity !== undefined && config.opacity !== null) {
                // 向后兼容：如果未设置background_opacity，则使用opacity作为背景透明度
                glassEffect.opacityTint = config.opacity
            }
            
            // 设置窗口整体透明度 - 根据规范，将opacity属性直接应用于窗口根元素
            if (config.opacity !== undefined && config.opacity !== null) {
                quickWindow.windowOpacity = config.opacity
            }
            
            // 立即更新边框颜色
            borderRect.border.color = Qt.darker(config.background_color, 1.2)

            // 更新窗口大小
            updateWindowSize()

            // 更新窗口位置
            if (config.position) {
                positionWindow()
            }
            
            // 重新加载应用列表以确保顺序正确
            loadApps()
        }

        function onApps_changed(newApps) {
            console.log("收到应用列表更新信号")
            apps = newApps
            loadApps()
        }

        function onVisibility_changed(visible) {
            if (visible) {
                showWindow()
            } else {
                hideWindow()
            }
        }
    }

    // 连接主窗口后端信号
    Connections {
        target: mainWindowBackend

        function onApp_list_updated(appsList) {
            console.log("收到应用列表更新信号（主窗口）")
            apps = appsList
            loadApps()
        }

        function onConfig_updated(newConfig) {
            console.log("收到配置更新信号（主窗口）")
            config = newConfig

            // 确保配置值有效
            if (config.opacity === undefined || config.opacity === null) {
                config.opacity = 0.9  // 窗口整体透明度，默认值为0.9
            }
            if (config.hover_scale === undefined || config.hover_scale === null) {
                config.hover_scale = 1.5
            }
            if (config.background_color === undefined || config.background_color === null) {
                config.background_color = "#FFFFFF"
            }
            if (config.background_opacity === undefined || config.background_opacity === null) {
                config.background_opacity = 0.3  // 背景毛玻璃透明度，默认值为0.3
            }
            if (config.rows === undefined || config.rows === null) {
                config.rows = 1  // 默认行数为1
            }
            if (config.cols === undefined || config.cols === null) {
                config.cols = 5  // 默认列数为5
            }
            if (config.icon_spacing === undefined || config.icon_spacing === null) {
                config.icon_spacing = 10  // 默认图标间距为10
            }

            // 更新界面
            // 根据配置中的show_labels设置来决定是否显示标签
            labelsVisible = config.show_labels === true
            
            // 立即更新背景颜色和透明度
            if (config.background_color) {
                glassEffect.colorTint = Qt.rgba(
                    parseInt(config.background_color.substr(1, 2), 16) / 255.0,
                    parseInt(config.background_color.substr(3, 2), 16) / 255.0,
                    parseInt(config.background_color.substr(5, 2), 16) / 255.0,
                    1.0
                )
            }
            // 使用专门的background_opacity参数来控制毛玻璃效果透明度，而不是混用opacity参数
            if (config.background_opacity !== undefined && config.background_opacity !== null) {
                glassEffect.opacityTint = config.background_opacity
            } else if (config.opacity !== undefined && config.opacity !== null) {
                // 向后兼容：如果未设置background_opacity，则使用opacity作为背景透明度
                glassEffect.opacityTint = config.opacity
            }
            
            // 设置窗口整体透明度 - 根据规范，将opacity属性直接应用于背景层，而不是整个窗口
            if (config.opacity !== undefined && config.opacity !== null) {
                quickWindow.windowOpacity = config.opacity
            }
            
            // 立即更新边框颜色
            borderRect.border.color = Qt.darker(config.background_color, 1.2)

            // 更新窗口大小
            updateWindowSize()

            // 更新窗口位置
            if (config.position) {
                positionWindow()
            }

            // 重新加载应用顺序和网格布局
            loadApps()
        }
    }
}