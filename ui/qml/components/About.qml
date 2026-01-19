import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 与启动页面完全相同的默认内容组件
Item {  // 改为Item以确保透明背景
    anchors.fill: parent

    // 主内容容器，添加边距以与其他组件保持一致
    Item {
        anchors.fill: parent
        anchors.margins: 10  // 添加与其他组件相同的边距
        Rectangle {
            anchors.fill: parent
            color: "#FFFFFF"  // 确保有明确的背景色
            radius: 8  // 添加圆角，与主窗口保持一致
        }

        Column {
            anchors.centerIn: parent
            spacing: 20

            Text {
                text: "QuickLauncher"
                color: "#007ACC"
                font.pixelSize: 32
                font.bold: true
            }

            Text {
                text: "一个现代化的 Windows 应用快捷启动器"
                color: "#000000"
                font.pixelSize: 16
            }

            Rectangle {
                width: 200
                height: 1
                color: "#CCCCCC"
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text {
                text: "请从左侧选择功能"
                color: "#666666"
                font.pixelSize: 14
            }

            // 快速操作按钮
            Column {
                spacing: 10
                anchors.horizontalCenter: parent.horizontalCenter

                // 应用管理按钮
                Rectangle {
                    width: 200
                    height: 40
                    radius: 5
                    color: "#007ACC"

                    Text {
                        anchors.centerIn: parent
                        text: "应用管理"
                        color: "#FFFFFF"
                        font.pixelSize: 14
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            // 通过全局方法访问contentLoader
                            if (typeof contentLoader !== 'undefined') {
                                contentLoader.source = "components/AppManagement.qml"
                            } else {
                                // 尝试通过window对象访问
                                console.log("切换到应用管理页面")
                            }
                        }
                        cursorShape: Qt.PointingHandCursor
                    }
                }

                // 快捷窗口管理按钮
                Rectangle {
                    width: 200
                    height: 40
                    radius: 5
                    color: "#4CAF50"

                    Text {
                        anchors.centerIn: parent
                        text: "快捷窗口管理"
                        color: "#FFFFFF"
                        font.pixelSize: 14
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (typeof contentLoader !== 'undefined') {
                                contentLoader.source = "components/QuickWindowManagement.qml"
                            } else {
                                console.log("切换到快捷窗口管理页面")
                            }
                        }
                        cursorShape: Qt.PointingHandCursor
                    }
                }
                
                // 主窗口设置按钮
                Rectangle {
                    width: 200
                    height: 40
                    radius: 5
                    color: "#2196F3"

                    Text {
                        anchors.centerIn: parent
                        text: "主窗口设置"
                        color: "#FFFFFF"
                        font.pixelSize: 14
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (typeof contentLoader !== 'undefined') {
                                contentLoader.source = "components/MainWindowManagement.qml"
                            } else {
                                console.log("切换到主窗口设置页面")
                            }
                        }
                        cursorShape: Qt.PointingHandCursor
                    }
                }
            }
        }
    }
}