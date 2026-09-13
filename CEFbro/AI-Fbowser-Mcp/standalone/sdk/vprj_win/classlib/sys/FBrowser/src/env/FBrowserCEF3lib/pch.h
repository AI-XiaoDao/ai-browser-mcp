// pch.h: 这是预编译标头文件。
// 下方列出的文件仅编译一次，提高了将来生成的生成性能。
// 这还将影响 IntelliSense 性能，包括代码完成和许多代码浏览功能。
// 但是，如果此处列出的文件中的任何一个在生成之间有更新，它们全部都将被重新编译。
// 请勿在此处添加要频繁更新的文件，这将使得性能优势无效。

#ifndef PCH_H
#define PCH_H

#include <windows.h>
#include <list>
#include <stdlib.h>
#include <atlconv.h>
#include <tchar.h>
#include <tlhelp32.h>
#include <wtypes.h>

#include <utility>
#include <chrono> 

#include "include/cef_client.h"
#include "include/cef_base.h"
#include "include/cef_app.h"
#include "include/cef_browser.h"
#include "include/cef_frame.h"
#include "include/cef_ssl_info.h"
#include "include/cef_dialog_handler.h"
#include "include/cef_jsdialog_handler.h"
#include "include/cef_menu_model.h"
#include "include/cef_context_menu_handler.h"
#include "include/cef_download_item.h"
#include "include/cef_download_handler.h"
#include "include/cef_auth_callback.h"

#include "include/cef_resource_bundle.h"
#include "include/cef_server.h"
#include "include/cef_response_filter.h"
#include "include/cef_parser.h"
#include "include/cef_request.h"
#include "include/cef_image.h"
#include "include/cef_task.h"

#include "include/cef_request_handler.h"
#include "include/cef_request_context.h"
#include "include/cef_request_context_handler.h"
#include "include/cef_command_line.h"
#include "include/cef_urlrequest.h"
#include "include/cef_x509_certificate.h"
#include "include/cef_response.h"
#include "include/cef_v8.h"
#include "include/cef_dom.h"
#include "include/cef_drag_data.h"
//待处理#include "include/cef_extension_handler.h"
#include "include/cef_stream.h"
#include "include/cef_render_handler.h"


#include "include/cef_waitable_event.h"

//待处理#include "include/fbrowser/fbro_wssclient.h"
//待处理#include "include/fbrowser/fbro_callback.h"

#include "include/internal/cef_win.h"

#include "FBroBase.h"
#include "FBroUnits.h"
#include "FBroTypes.h"

#include "FBroOnceClosureTask.h"



// 添加要在此处预编译的标头
#endif //PCH_H






