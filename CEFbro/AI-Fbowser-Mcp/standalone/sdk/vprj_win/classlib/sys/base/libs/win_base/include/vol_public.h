
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_PUBLIC_H__
#define __VOL_PUBLIC_H__

// 用作在窗口的用户自定义数据中标志本窗口需要过滤自身及下属子窗口的输入信息.
// 设置了此标志的窗口必须处理 MWM_PRE_FILTER_INPUT_MSG 消息
#define VWD_INPUT_MSG_FILTER_MARK  19731115
#define _VOL_MSG_ACK  19731115  // 用作在消息应答时使用

#define _MW_MSG_FIRST  (WM_APP + 0x2000)  // 自定义消息的首值
#define MWM_PRE_FILTER_INPUT_MSG           (_MW_MSG_FIRST - 1)  // 用作发送输入信息过滤消息,已经被过滤返回 _VOL_MSG_ACK ,未过滤返回0. wParam: 提供所欲过滤的信息指针(MSG*); lParam: _VOL_MSG_ACK
#define MWM_GET_WND_OBJECT                 (_MW_MSG_FIRST - 2)  // 用作返回所指定窗口对应的对象指针,成功返回 _VOL_MSG_ACK ,否则返回0. wParam: 提供调用参数指针(_VOL_GET_WND_OBJECT_PARAM*); lParam: _VOL_MSG_ACK
    typedef struct
    {
        const TCHAR* m_szFindClassName;  // 提供所欲查找的类名
        void* m_pWndObject;  // 用作返回所找到的对象指针
    }
    _VOL_GET_WND_OBJECT_PARAM;
#define MWM_GET_WND_GROUP_NUMBER           (_MW_MSG_FIRST - 3)  // 用作返回所指定窗口的设计时分组编号,成功返回 _VOL_MSG_ACK ,否则返回0. wParam: 提供用作存放所返回分组编号的整数指针(INT*); lParam: _VOL_MSG_ACK
#define MWM_SET_WND_GROUP_NUMBER           (_MW_MSG_FIRST - 4)  // 用作设置所指定窗口的设计时分组编号,成功返回 _VOL_MSG_ACK ,否则返回0. wParam: 提供所欲设置到的分组编号; lParam: _VOL_MSG_ACK
#define MWM_REGISTER_WINDOW_PROC_FILTER    (_MW_MSG_FIRST - 5)  // 用作登记窗口过程过滤器,成功返回 _VOL_MSG_ACK ,否则返回0. wParam: 提供过滤器对象指针(IVolWindowProcFilter*); lParam: _VOL_MSG_ACK
#define MWM_UNREGISTER_WINDOW_PROC_FILTER  (_MW_MSG_FIRST - 6)  // 用作取消窗口过程过滤器登记,成功返回 _VOL_MSG_ACK ,否则返回0. wParam: 提供过滤器对象指针(IVolWindowProcFilter*); lParam: _VOL_MSG_ACK
// 选择夹组件相关
#define MWM_IS_ON_CHILD_TAB_SWITCHER       (_MW_MSG_FIRST - 7)  // 仅被选择夹类的组件在设计时使用,用作返回所指定的在其客户区内的位置是否位于子夹头上,且在此位置处单击将改变当前子夹. 确定位于子夹头上返回 _VOL_MSG_ACK ,否则返回0.
                                                                // wParam: 提供检测位置(相对客户区左上角),通过GET_X_LPARAM和GET_Y_LPARAM取出XY位置; lParam: _VOL_MSG_ACK
#define MWM_GET_CURRENT_CHILD_TAB_INDEX    (_MW_MSG_FIRST - 8)  // 仅被选择夹类的组件使用,用作返回其当前子夹索引. 该组件为选择夹类组件返回 _VOL_MSG_ACK ,否则返回0.  wParam: 提供指针(INT*),需要将当前子夹索引值填入其中; lParam: _VOL_MSG_ACK
#define MWM_ON_CURRENT_CHILD_TAB_CHANGED   (_MW_MSG_FIRST - 9)  // 仅被选择夹类的组件使用,用作通知所有直接/间接父窗口其当前子夹已经被改变,成功处理返回 _VOL_MSG_ACK ,此时将不再向后续父组件发送本通知,否则返回0. wParam: 提供本选择夹窗口句柄; lParam: _VOL_MSG_ACK
#define MWM_RECORD_WND_VISIBLE_STATE       (_MW_MSG_FIRST - 10)  // 用作记录所指定窗口组件的可视状态,成功返回 _VOL_MSG_ACK ,否则返回0. wParam: 提供需要记录的组件可视状态(BOOL_P); lParam: _VOL_MSG_ACK
#define MWM_GET_WND_RECORDED_VISIBLE_STATE  (_MW_MSG_FIRST - 11)  // 用作记录所指定窗口组件的可视状态,成功返回 _VOL_MSG_ACK ,否则返回0. wParam: 提供指针(BOOL*),需要将组件先前记录的可视状态填入其中; lParam: _VOL_MSG_ACK
#define MWM_CEF_BROWSER_WORK_MSG           (_MW_MSG_FIRST - 12)  // CEF浏览器的工作通知消息

#endif
