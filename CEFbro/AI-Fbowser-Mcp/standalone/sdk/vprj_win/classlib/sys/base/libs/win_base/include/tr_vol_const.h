
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __TR_VOL_CONST_H__
#define __TR_VOL_CONST_H__

// 逻辑值立即数文本
#define _T_V_TRUE  _T ("真")
#define _T_V_FALSE  _T ("假")

#define _T_MEMORY_LEAK_REPORT_DDDDF  _T ("[内存监测]: 在缓存池中峰值分配内存块数/缓存池总尺寸(预分配块数): ") _TF_NP _T (" / ") _TF_NP _T (" , ") _T ("总共分配了 ") _TF_NP _T (" 次内存,有 ") _TF_NP _T (" 次在缓存池中分配,比例为 %.8G%% .\r\n")
#define _T_MEMORY_LEAK_REPORT_D  _T ("[内存监测]: 未释放垃圾内存块数目: ") _TF_NP _T ("\r\n")
#define _T_LOAD_EXTERN_DLL_FAILED_S  _T ("载入运行时所需要的外部动态链接库文件\"%s\"失败!")
#define _T_NOT_FOUND_EXTERN_FUNCTION_SS  _T ("在外部动态链接库\"%s\"中未找到所需要的输出函数\"%s\"!")
#define _T_UNKNOWN_DUMPING_VOL_OBJECT_SX  _T ("无法解析的对象数据,其输出类名为: \"%s\", 地址为: 0x") _TF_HP
#define _T_BIN_BYTES_DUMPED1_D  _T ("<字节集> 总共 %d 个字节:")
#define _T_BIN_BYTES_DUMPED2_DDD  _T ("<字节集> 总共 %d 个字节,输出了 %d 个,还有 %d 个未被输出.")
#define _T_ARY_ELEMENTS_DUMPED1_D  _T ("<数组> 总共 %d 个成员:")
#define _T_ARY_ELEMENTS_DUMPED2_DDD  _T ("<数组> 总共 %d 个成员,输出了 %d 个,还有 %d 个未被输出.")
#define _T_VOL_OBJECT_DSX _T ("\r\n%d. 对象输出类名: \"%s\", 地址: 0x") _TF_HP
#define _T_VOL_OBJECT_CONTENT  _T (", 内容:\r\n")
#define _T_EMPTY_VOL_OBJECT _T (", 为空对象")
#define _T_VARIANT_EMPTY  _T ("{ 空 }")
#define _T_VARIANT_UNKNOWN_TYPE  _T ("未知类型 }")
#define _T_VARIANT_REF  _T (", 参考")
#define _T_VARIANT_ARRAY  _T (", 数组")
#define _T_VARIANT_UNKNOWN_VALUE  _T ("未知值")
#define _T_VARIANT_NULL_STR_POINTER  _T ("空文本指针")
#define _T_DEBUG_MSG_BOX_CAPTION  _T ("调试输出信息:")
#define _T_NULL_VOL_OBJECT  _T ("[空]")
#define _T_RUNTIME_ASSERT_FAIL  _T ("运行时校验失败")
#define _T_VOL_EXCEPTION_DUMP_DS  _T ("代码: %d; 描述: %s")
#define _T_LOAD_VOL_COM_DLL_FAILED_S  _T ("载入火山部件DLL\"%s\"失败,程序无法继续运行将强制退出!")
#define _T_GET_VOL_COM_DLL_FUNC_TABLE_FAILED_S  _T ("获取火山部件DLL\"%s\"中的功能输出表失败,程序无法继续运行将强制退出!")
#define _T_FATAL_RUNTIME_ERROR_CAPTION  _T ("运行时严重错误:")
#ifdef _DEBUG
    #define _T_FOUND_NOT_MATCH_SYS_CLASSES_S  _T ("调用火山部件DLL\"%s\"中的功能时发现以下系统模块类在两者之间不匹配,请重新编译更新该部件DLL.") _T ("\r\n") _T ("注: 也有可能是因为某些类的调试版和发布版之间数据格式不相同的原因,不要直接将这些类用在部件DLL接口中,如确需使用请自行定义一个新类来继承它,然后覆写(转接调用原方法)所欲使用的相关方法后改为使用该新继承类即可.") _T ("\r\n") _T ("\r\n")
#else
    #define _T_FOUND_NOT_MATCH_SYS_CLASSES_S  _T ("调用火山部件DLL\"%s\"中的功能时存在系统模块类在两者之间不匹配,请重新编译更新该部件DLL.")
#endif

// 火山线程池相关:
#define _T_VTP_START_NEW_THREAD_FROM_POOL_SUCCEEDED_D  _T ("[线程池]: 从线程池中重新启动已有空闲线程 %d 成功.")
#define _T_VTP_START_NEW_THREAD_FAIL  _T ("[线程池]: 启动新线程失败.")
#define _T_VTP_CREATE_AND_START_NEW_THREAD_SUCCEEDED_D _T ("[线程池]: 全新创建并启动一个新线程 %d 成功.")
#define _T_VTP_THREAD_FREE_INTO_IDLE_STATE_D  _T ("[线程池]: 线程 <%d> 停止执行进入了空闲状态.")
#define _T_VTP_TOO_LONG_REST_TIME_THREAD_DESTROIED_DD  _T ("[线程池]: 线程 <%d> 由于处于空闲状态 %d 毫秒超出限制而被销毁.")
#define _T_VTP_ENDED_THREAD_DESTROIED_D  _T ("[线程池]: 线程 <%d> 由于运行结束而被销毁.")
#define _T_VTP_TOO_MANY_THREAD_DESTROIED_D  _T ("[线程池]: 线程 <%d> 由于已有空闲线程数目过多而被销毁.")
#define _T_VTP_DUMP_FORMAT_DDDD  _T ("[线程池]: 全部线程数目: %d / 空闲: %d; 正在运行: %d; 运行结束: %d")

// 提供当前所支持的所有格式图片文件的过滤器文本
#define _T_SUPPORTED_IMAGE_FILE_FILTERS  \
        _T ("所有图片文件|*.gif;*.bmp;*.emf;*.wmf;*.jpg;*.jpeg;*.png;*.tif;*.ico|GIF文件(*.gif)|*.gif|BMP文件(*.bmp)|*.bmp|EMF文件(*.emf)|*.emf|WMF文件(*.wmf)|*.wmf|JPG文件(*.jpg;*.jpeg)|*.jpg;*.jpeg|PNG文件(*.png)|*.png|TIFF文件(*.tif)|*.tif|ICO文件(*.ico)|*.ico|")

#endif
