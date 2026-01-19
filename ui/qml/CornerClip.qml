import QtQuick
import Qt5Compat.GraphicalEffects

Item {
    id: root
    
    // 定义哪些角需要圆角
    property bool topLeft: false
    property bool topRight: false
    property bool bottomLeft: false
    property bool bottomRight: false
    property real radius: 8
    
    // 要应用圆角效果的内容
    default property alias content: container.data
    
    Item {
        id: container
        anchors.fill: parent
    }
    
    // 使用Clip组件来实现特定角的圆角效果
    Item {
        id: clipItem
        anchors.fill: parent
        clip: true
        
        // 创建一个路径来定义圆角区域
        layer.enabled: true
        layer.effect: OpacityMask {
            maskSource: Item {
                width: root.width
                height: root.height
                
                // 创建一个具有指定圆角的路径
                Canvas {
                    id: maskCanvas
                    width: root.width
                    height: root.height
                    
                    onPaint: {
                        // 检查宽高是否有效
                        if (width <= 0 || height <= 0) return;
                        
                        var ctx = getContext("2d");
                        ctx.reset();
                        
                        // 开始路径
                        ctx.beginPath();
                        
                        // 从左上角开始，根据属性决定是否圆角
                        ctx.moveTo(root.topLeft ? root.radius : 0, 0);
                        
                        // 右上角
                        if (root.topRight) {
                            ctx.arc(width - root.radius, root.radius, root.radius, -Math.PI/2, 0);
                        } else {
                            ctx.lineTo(width, 0);
                        }
                        
                        // 右下角
                        if (root.bottomRight) {
                            ctx.arc(width - root.radius, height - root.radius, root.radius, 0, Math.PI/2);
                        } else {
                            ctx.lineTo(width, height);
                        }
                        
                        // 左下角
                        if (root.bottomLeft) {
                            ctx.arc(root.radius, height - root.radius, root.radius, Math.PI/2, Math.PI);
                        } else {
                            ctx.lineTo(0, height);
                        }
                        
                        // 左上角
                        if (root.topLeft) {
                            ctx.arc(root.radius, root.radius, root.radius, Math.PI, Math.PI*3/2);
                        } else {
                            ctx.lineTo(0, 0);
                        }
                        
                        ctx.closePath();
                        ctx.fillStyle = "#ffffff";
                        ctx.fill();
                    }
                    
                    // 当属性变化时重新绘制
                    Component.onCompleted: requestPaint()
                    
                    // 当尺寸或圆角属性变化时重新绘制
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    Connections {
                        target: root
                        function onTopLeftChanged() { maskCanvas.requestPaint(); }
                        function onTopRightChanged() { maskCanvas.requestPaint(); }
                        function onBottomLeftChanged() { maskCanvas.requestPaint(); }
                        function onBottomRightChanged() { maskCanvas.requestPaint(); }
                        function onRadiusChanged() { maskCanvas.requestPaint(); }
                    }
                }
            }
        }
        
        // 重新添加容器内容
        Item {
            anchors.fill: parent
            anchors.margins: 1  // 小的边距以确保渲染正确
            
            // 重新添加内容
            data: root.content
        }
    }
}