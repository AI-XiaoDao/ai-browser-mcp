#pragma once
#include <Windows.h>

// 基础设置信息结构
struct FBroInitSettings
{
	BOOL no_sandbox;						 // 沙箱
	char* browser_subprocess_path = NULL;	 // 子进程启动的独立可执行文件的路径
	char* framework_dir_path = NULL;		 // CEF框架目录的路径
	char* main_bundle_path = NULL;			 // 主包的路径
	BOOL multi_threaded_message_loop;		 // 消息循环
	BOOL external_message_pump;				 // 外部消息泵
	BOOL windowless_rendering_enabled;		 // 离屏渲染
	BOOL command_line_args_disabled;		 // 禁用命令参数
	char* cache_path = NULL;				 // 缓存路径
	//char* root_cache_path = NULL;			 // 根目录
	BOOL persist_session_cookies;			 // 保持cookie
	char* user_agent = NULL;				 // UA
	char* user_agent_product = NULL;		 // 134新加
	char* locale = NULL;					 // 语言环境
	char* log_file = NULL;					 // 日志目录
	int log_severity;						 // 日志模式
	int log_items;							 // 134新加
	char* javascript_flags = NULL;			 //
	char* resources_dir_path = NULL;		 // 资源路径
	char* locales_dir_path = NULL;			 // 语言路径
	int remote_debugging_port = 0;			 // 远程端口
	int uncaught_exception_stack_size = 0;	 //
	int background_color = 0;				 // 背景颜色
	char* accept_language_list = NULL;		 // 语言清单
	char* cookieable_schemes_list = NULL;	 // 启用cookie计划清单参数
	int cookieable_schemes_exclude_defaults; // 启用cookie计划_排除默认参数
	char* chrome_policy_id = NULL;			 // 134新加
	int chrome_app_icon_id = 0;				 // 134新加
	int disable_signal_handlers = 0;		 // 134新加

	BOOL enable_auto_multiple = false;       // 启用自动多例模式，启用后多exe运行会自动在缓存目录下创建以temp开头的子缓存目录，避免缓存文件冲突
};

// 浏览器设置结构体

struct FBroBrowserSetting
{
	BOOL is_null;
	int windowless_frame_rate = 0;

	char* standard_font_family = NULL;
	char* fixed_font_family = NULL;
	char* serif_font_family = NULL;
	char* sans_serif_font_family = NULL;
	char* cursive_font_family = NULL;
	char* fantasy_font_family = NULL;

	int default_font_size = 0;
	int default_fixed_font_size = 0;
	int minimum_font_size = 0;
	int minimum_logical_font_size = 0;

	char* default_encoding = NULL;

	int remote_fonts = 0; //-1 STATE_DISABLED 0 STATE_DEFAULT 1 STATE_ENABLED
	int javascript = 0;
	int javascript_close_windows = 0;
	int javascript_access_clipboard = 0;
	int javascript_dom_paste = 0;

	int image_loading = 0;
	int image_shrink_standalone_to_fit = 0;
	int text_area_resize = 0;
	int tab_to_links = 0;
	int local_storage = 0;
	int databases = 0;
	int webgl = 0;
	int background_color = 0;
	int chrome_status_bubble = 0;
	int chrome_zoom_bubble = 0; // 134新加

};


typedef struct E_WINDOWS_INFO
{
	BOOL is_null;
	DWORD ex_style;
	char* window_name = NULL;
	DWORD style;
	int x;
	int y;
	int width;
	int height;
	HWND parent_window; // 父窗口句柄
	HMENU menu;			// 菜单句柄
	BOOL windowless_rendering_enabled;
	BOOL shared_texture_enabled;
	BOOL external_begin_frame_enabled;
	HWND window;					 // 窗口句柄
	char* parent_window_name = NULL; // 父窗口名
	int runtime_style;				 // 运行风格
} *PTELIB_WINDOWS_INFO;