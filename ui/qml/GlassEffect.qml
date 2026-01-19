import QtQuick
import Qt5Compat.GraphicalEffects

// 毛玻璃效果组件 - 可复用的效果实现
Item {
    id: control

    // 毛玻璃效果参数
    property real radiusBlur: 32
    property real opacityTint: 0.2
    property real opacityNoise: 0.02
    property color colorTint: "#FFFFFF"
    property real luminosity: 0.1
    property alias radiusBg: background.radius  // 通过外部控制圆角半径
    property Item sourceItem: null
    property bool enableNoise: false  // 添加开关来控制是否启用噪声效果

    // 捕获背景图像
    ShaderEffectSource {
        id: __source
        anchors.fill: parent
        visible: false
        sourceItem: control.sourceItem || parent // 如果未指定sourceItem，则使用parent作为源
        sourceRect: Qt.rect(control.x, control.y, control.width, control.height)
        // smooth: true
        // hideSource: true
    }

    // 模糊处理
    GaussianBlur {
        id: __blur
        anchors.fill: parent
        source: __source
        radius: control.radiusBlur
        samples: control.radiusBlur * 2 + 1  // 增加采样数以提高模糊质量
        transparentBorder: true
    }

    // 背景亮度层
    Rectangle {
        id: background
        anchors.fill: parent
        color: Qt.rgba(1, 1, 1, control.luminosity)
        radius: control.radiusBg  // 使用外部传入的圆角半径
        clip: true  // 确保内容被圆角裁剪
    }

    // 颜色色调层
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(control.colorTint.r, control.colorTint.g, control.colorTint.b, control.opacityTint)
        radius: background.radius
        clip: true  // 确保色调层也被圆角裁剪
    }

    // 噪声效果层 - 只有在enableNoise为true时才启用
    Image {
        id: __noiseImage
        anchors.fill: parent
        source: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAEnQAABJ0Ad5mH3gAAAGHaVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49J++7vycgaWQ9J1c1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCc/Pg0KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyI+PHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj48cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0idXVpZDpmYWY1YmRkNS1iYTNkLTExZGEtYWQzMS1kMzNkNzUxODJmMWIiIHhtbG5zOnRpZmY9Imh0dHA6Ly9ucy5hZG9iZS5jb20vdGlmZi8xLjAvIj48dGlmZjpPcmllbnRhdGlvbj4xPC90aWZmOk9yaWVudGF0aW9uPjwvcmRmOkRlc2NyaXB0aW9uPjwvcmRmOlJERj48L3g6eG1wbWV0YT4NCjw/eHBhY2tldCBlbmQ9J3cnPz4slJgLAAAMNElEQVRYR02XW1NTd9vGf0nYZEFMVha7JBAIYYihEQVSUQS0VpV2ppV22h48aHvUg2Y8aMfTtjNtT9vT2Zk6bUfa4QFEKZWIsgm7ECKQHZu1FpiQQAx5DnyfzHv6n//Jvbl+13Vrvv/++5zRaOSPP/7giy++wGQyMTw8TCgUoquri2QySSgUorm5mcbGRh4/fozT6cTtdvPgwQMMBgPnzp0DYHR0FEmSiEag=="  // 噪声图片的base64编码
        fillMode: Image.Tile
        opacity: control.opacityNoise
        visible: control.enableNoise
        clip: true  // 确保噪声层也被圆角裁剪
    }

    // 将模糊效果应用到整个组件
    layer.enabled: true
    layer.effect: __blur
}