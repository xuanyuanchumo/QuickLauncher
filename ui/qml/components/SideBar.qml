import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import ".."

// 侧边导航栏组件
Item {  // 改为Item以避免与GlassEffect的类型冲突
    id: sideBar
    width: 200
    height: parent.height
    // 定义属性以与主窗口通信
    property var mainWindowConfig: ({})
    property var contentLoader: null
    property string currentSource: ""
    property int appCount: 0
    property alias statusText: statusTextItem
    property alias appCountText: appCountTextItem

    // 信号定义，用于与父级交互
    signal appManagementClicked()
    signal quickWindowManagementClicked()
    signal mainWindowManagementClicked()
    signal aboutClicked()

    // 监听mainWindowConfig变化，更新毛玻璃效果
    onMainWindowConfigChanged: {
        if (mainWindowConfig) {
            updateSidebarEffects()
        }
    }

    // 更新侧边栏效果
    function updateSidebarEffects() {
        if (mainWindowConfig && typeof mainWindowConfig === 'object') {
            // 由于现在直接继承主窗口毛玻璃效果，无需单独更新
        }
    }

    // 主容器
    Rectangle {
        id: sidebarContainer
        anchors.fill: parent
        color: "transparent"

        // 导航栏背景容器 - 用于继承主窗口毛玻璃效果
        Item {
            id: sidebarBackground
            anchors.fill: parent
        }

        // 导航栏内容容器 - 保持不透明以确保内容清晰可见
        Item {
            anchors.fill: parent
            z: 1  // 确保内容在毛玻璃效果之上

            Column {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                // 标题
                Text {
                    width: parent.width
                    text: "QuickLauncher"
                    color: "#007ACC"  // 使用蓝色文字以确保对比度
                    font.pixelSize: 20
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    padding: 10
                }

                // 分隔线
                Rectangle {
                    width: parent.width
                    height: 1
                    color: "#CCCCCC"
                }

                // 应用管理按钮
                Rectangle {
                    id: appBtn
                    width: parent.width
                    height: 40
                    color: currentSource === "" ||
                           currentSource.toString().indexOf("AppManagement") !== -1 ?
                           "#094771" : "#F0F0F0"  // 使用更亮的背景色以确保对比度
                    radius: 3

                    Text {
                        anchors.centerIn: parent
                        text: "应用管理"
                        color: currentSource === "" ||
                               currentSource.toString().indexOf("AppManagement") !== -1 ?
                                   "#FFFFFF" : "#000000"  // 使用黑色文字以确保对比度
                        font.pixelSize: 14
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            console.log("加载应用管理页面")
                            appManagementClicked()
                        }
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onEntered: {
                            if (currentSource.toString().indexOf("AppManagement") === -1) {
                                parent.color = "#D0D0D0"
                            }
                        }
                        onExited: {
                            if (currentSource.toString().indexOf("AppManagement") === -1) {
                                parent.color = "#F0F0F0"
                            }
                        }
                    }
                }

                // 快捷窗口管理按钮
                Rectangle {
                    id: quickBtn
                    width: parent.width
                    height: 40
                    color: currentSource.toString().indexOf("QuickWindowManagement") !== -1 ?
                           "#094771" : "#F0F0F0"  // 使用更亮的背景色以确保对比度
                    radius: 3

                    Text {
                        anchors.centerIn: parent
                        text: "快捷窗口设置"
                        color: currentSource.toString().indexOf("QuickWindowManagement") !== -1 ?
                               "#FFFFFF" : "#000000"  // 使用黑色文字以确保对比度
                        font.pixelSize: 14
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            console.log("加载快捷窗口设置页面")
                            quickWindowManagementClicked()
                        }
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onEntered: {
                            if (currentSource.toString().indexOf("QuickWindowManagement") === -1) {
                                parent.color = "#D0D0D0"
                            }
                        }
                        onExited: {
                            if (currentSource.toString().indexOf("QuickWindowManagement") === -1) {
                                parent.color = "#F0F0F0"
                            }
                        }
                    }
                }

                // // 主窗口设置按钮
                // Rectangle {
                //     id: mainSettingsBtn
                //     width: parent.width
                //     height: 40
                //     color: currentSource.toString().indexOf("MainWindowManagement") !== -1 ?
                //            "#094771" : "#F0F0F0"  // 使用更亮的背景色以确保对比度
                //     radius: 3
                //
                //     Text {
                //         anchors.centerIn: parent
                //         text: "主窗口设置"
                //         color: currentSource.toString().indexOf("MainWindowManagement") !== -1 ?
                //            "#FFFFFF" : "#000000"  // 使用黑色文字以确保对比度
                //         font.pixelSize: 14
                //     }
                //
                //     MouseArea {
                //         anchors.fill: parent
                //         onClicked: {
                //             console.log("加载主窗口设置页面")
                //             mainWindowManagementClicked()
                //         }
                //         hoverEnabled: true
                //         cursorShape: Qt.PointingHandCursor
                //         onEntered: {
                //             if (currentSource.toString().indexOf("MainWindowManagement") === -1) {
                //                 parent.color = "#D0D0D0"
                //             }
                //         }
                //         onExited: {
                //             if (currentSource.toString().indexOf("MainWindowManagement") === -1) {
                //                 parent.color = "#F0F0F0"
                //             }
                //         }
                //     }
                // }

                // 关于按钮
                Rectangle {
                    id: aboutBtn
                    width: parent.width
                    height: 40
                    color: currentSource === "" || currentSource.toString().indexOf("About") !== -1 ?
                           "#094771" : "#F0F0F0"  // 使用更亮的背景色以确保对比度
                    radius: 3

                    Text {
                        anchors.centerIn: parent
                        text: "关于"
                        color: currentSource === "" || currentSource.toString().indexOf("About") !== -1 ?
                           "#FFFFFF" : "#000000"  // 使用黑色文字以确保对比度
                        font.pixelSize: 14
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            console.log("加载关于页面")
                            aboutClicked()
                        }
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onEntered: {
                            if (currentSource.toString().indexOf("About") === -1) {
                                parent.color = "#D0D0D0"
                            }
                        }
                        onExited: {
                            if (currentSource.toString().indexOf("About") === -1) {
                                parent.color = "#F0F0F0"
                            }
                        }
                    }
                }

                // 占位空间 - 填充剩余空间
                Item {
                    width: parent.width
                    height: parent.height - y - 40
                }

                // 状态栏 - 固定在导航栏底部
                Rectangle {
                    id: statusBar
                    width: parent.width - 10  // 减去边距
                    height: 30
                    color: "transparent"  // 改为透明以支持背景效果
                    x: 5  // 添加左边距以匹配整体布局
                    y: parent.height - height - 5  // 定位到底部并留出边距

                    // 状态栏背景容器 - 用于继承主窗口毛玻璃效果
                    Item {
                        id: statusBarBackground
                        anchors.fill: parent
                    }

                    // 状态栏内容容器 - 保持不透明以确保内容清晰可见，且在毛玻璃效果之上
                    Item {
                        anchors.fill: parent
                        z: 1  // 确保内容在毛玻璃效果之上

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 5
                            spacing: 5

                            Text {
                                id: statusTextItem
                                Layout.fillWidth: true
                                color: "#666666"  // 使用深灰色文字以确保对比度
                                font.pixelSize: 12
                                text: "就绪"
                            }

                            Text {
                                id: appCountTextItem
                                Layout.rightMargin: 5
                                color: "#666666"  // 使用深灰色文字以确保对比度
                                font.pixelSize: 12
                                text: "应用: " + appCount
                            }
                        }
                    }
                }
            }

            // 右侧边框
            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: "#CCCCCC"
            }
        }
    }
}