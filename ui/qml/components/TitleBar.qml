import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import ".."

// 标题栏组件
Item {
    id: titleBarComponent
    height: 30
    property alias titleText: windowTitle.text
    property var config: ({})
    property var onMinimize: function() {}
    property var onMaximize: function() {}
    property var onClose: function() {}
    property bool isMaximized: false
    property var window: null  // 添加窗口引用属性，用于拖拽功能

    // 信号定义，用于与父级交互
    signal minimizeRequested()
    signal maximizeRequested()
    signal closeRequested()

    // 标题栏毛玻璃背景容器
    Item {
        id: titleBarBackground
        anchors.fill: parent
        z: 0  // 毛玻璃背景层级设为0

    }

    // 标题栏整体容器 - 设置为高于内容区域的层级
    Rectangle {
        id: titleBarContainer
        anchors.fill: parent
        color: "transparent"
        z: 5  // 确保标题栏在内容之上，根据经验教训设置为5以上

        // 标题栏内容容器 - 确保在毛玻璃效果之上
        Item {
            id: titleBarContent
            anchors.fill: parent
            z: 4  // 确保内容在毛玻璃效果之上

            // 使用水平布局确保内容从左到右排列
            Row {
                anchors.fill: parent
                spacing: 0
                // 确保内容左对齐，右侧空间由弹性项填充
                layoutDirection: Qt.LeftToRight

                // 窗口标题
                Text {
                    id: windowTitle
                    text: "QuickLauncher - 主窗口"
                    color: "#ff0000"
                    font.pixelSize: 12
                    verticalAlignment: Text.AlignVCenter
                    anchors.verticalCenter: parent.verticalCenter
                    leftPadding: 10  // 添加左边距
                }


                // 空间填充项，将控制按钮推到右侧
                Item {
                    id: titleBarSpacer
                    height: parent.height
                    width: parent.width - windowTitle.width- 90
                    z: 6
                    Layout.fillWidth: true
                }

                // 控制按钮容器 - 放置在右侧
                Row {
                    id: controlButtonsContainer
                    height: parent.height
                    z: 6  // 确保按钮在毛玻璃背景之上，层级高于标题栏容器
                    spacing: 0

                    // 最小化按钮
                    Rectangle {
                        id: minimizeButton
                        width: 30
                        height: parent.height
                        color: "transparent"  // 初始为透明
                        radius: 0
                        border.color: "#FFFFFF"
                        border.width: 0

                        Text {
                            anchors.centerIn: parent
                            text: "_"  // 使用下划线作为最小化图标
                            color: "#000000"  // 黑色文字，符合规范
                            font.pixelSize: 16
                            font.bold: true
                        }

                        MouseArea {
                            id: minimizeBtnMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onEntered: {
                                minimizeButton.color = "#B0B0B0"  // 悬停时变灰
                            }
                            onExited: {
                                minimizeButton.color = "transparent"  // 恢复透明背景，符合规范
                            }
                            onClicked: {
                                minimizeRequested()
                            }
                        }
                    }

                    // 最大化按钮
                    Rectangle {
                        id: maximizeButton
                        width: 30
                        height: parent.height
                        color: "transparent"  // 初始为透明
                        radius: 0
                        border.color: "#FFFFFF"
                        border.width: 0

                        Text {
                            anchors.centerIn: parent
                            text: titleBarComponent.isMaximized ? "O" : "口"  // O表示还原，口表示最大化
                            color: "#000000"  // 黑色文字，符合规范
                            font.family: "Arial"
                            font.bold: true
                            font.pixelSize: 10
                        }

                        MouseArea {
                            id: maximizeBtnMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onEntered: {
                                maximizeButton.color = "#B0B0B0"  // 悬停时变灰
                            }
                            onExited: {
                                maximizeButton.color = "transparent"  // 恢复透明背景，符合规范
                            }
                            onClicked: {
                                maximizeRequested()
                            }
                        }
                    }

                    // 关闭按钮
                    Rectangle {
                        id: closeButton
                        width: 30
                        height: parent.height
                        color: "transparent"  // 透明背景，符合规范
                        radius: 0
                        border.color: "#FFFFFF"
                        border.width: 0

                        Text {
                            anchors.centerIn: parent
                            text: "X"  // 使用X作为关闭图标
                            color: "#ff0000"  // 红色文字，符合规范
                            font.pixelSize: 12
                            font.bold: true
                        }

                        MouseArea {
                            id: closeBtnMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onEntered: {
                                closeButton.color = "#B0B0B0"  // 悬停时变红
                            }
                            onExited: {
                                closeButton.color = "transparent"  // 恢复背景，符合规范
                            }
                            onClicked: {
                                closeRequested()
                            }
                        }
                    }
                }
            }

            // 窗口拖拽功能 - 覆盖整个标题栏区域，除了控制按钮区域
            MouseArea {
                id: dragArea
                anchors.fill: parent
                // 设置右边距，为控制按钮留出交互空间
                anchors.rightMargin: controlButtonsContainer.width
                hoverEnabled: true
                
                property point clickPos: "0,0"
                
                onPressed: {
                    clickPos = Qt.point(mouse.x, mouse.y)
                    // 检查窗口是否已定义并支持拖拽
                    if (window) {
                        if (window.visibility === Window.Maximized) {
                            // 如果窗口最大化，则恢复到正常大小并调整位置
                            window.showNormal()
                            
                            // 计算点击位置在窗口中的相对位置（0到1之间）
                            var relativeX = mouse.x / titleBarComponent.width
                            
                            // 设置新的窗口位置，确保点击位置对应到新窗口的相同的相对位置
                            window.x = mouse.x - (relativeX * window.width)
                            window.y = mouse.y - 10  // 10是标题栏的高度
                        }
                        
                        // 开始系统拖拽操作
                        window.startSystemMove()
                    }
                }
            }
        }
    }
}