#pragma once
#ifndef FBROWSER_COMMAND_H_
#define FBROWSER_COMMAND_H_

class FBroString;

#ifndef _FBROELIB

DLLEXPORT CefRefPtr<CefCommandLine> TEXPORTS FBroHsCommandLine_CreateCommandLine();
DLLEXPORT CefRefPtr<CefCommandLine> TEXPORTS FBroHsCommandLine_GetGlobalCommandLine();
DLLEXPORT BOOL TEXPORTS FBroHsCommandLine_IsValid(CefRefPtr<CefCommandLine> cmd);
DLLEXPORT BOOL TEXPORTS FBroHsCommandLine_IsReadOnly(CefRefPtr<CefCommandLine> cmd);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsCommandLine_GetString(CefRefPtr<CefCommandLine> cmd);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsCommandLine_GetProgram(CefRefPtr<CefCommandLine> cmd);
DLLEXPORT void TEXPORTS FBroHsCommandLine_SetProgram(CefRefPtr<CefCommandLine> cmd, const CefString& program);
DLLEXPORT BOOL TEXPORTS FBroHsCommandLine_HasSwitches(CefRefPtr<CefCommandLine> cmd);
DLLEXPORT BOOL TEXPORTS FBroHsCommandLine_HasSwitche(CefRefPtr<CefCommandLine> cmd, const CefString& name);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsCommandLine_GetSwitchValue(CefRefPtr<CefCommandLine> cmd, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsCommandLine_AppendSwitch(CefRefPtr<CefCommandLine> cmd, const CefString& name);
DLLEXPORT void TEXPORTS FBroHsCommandLine_AppendSwitchWithValue(CefRefPtr<CefCommandLine> cmd, const CefString& name, const CefString& value);
DLLEXPORT BOOL TEXPORTS FBroHsCommandLine_HasArguments(CefRefPtr<CefCommandLine> cmd);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsCommandLine_GetArguments(CefRefPtr<CefCommandLine> cmd);
DLLEXPORT void TEXPORTS FBroHsCommandLine_AppendArgument(CefRefPtr<CefCommandLine> cmd, const CefString& arguments);
DLLEXPORT void TEXPORTS FBroHsCommandLine_PrependWrapper(CefRefPtr<CefCommandLine> cmd, const CefString& wrapper);

//启用单进程模式，仅调试模式下有效
DLLEXPORT void TEXPORTS FBroHsCommandLine_EnableSingleProcess(CefRefPtr<CefCommandLine> cmd);

//启用摄像头
DLLEXPORT void TEXPORTS FBroHsCommandLine_EnableMediaStream(CefRefPtr<CefCommandLine> cmd);

//启用跨域模式,跨框架操作
DLLEXPORT void TEXPORTS FBroHsCommandLine_EnableCrossFrame(CefRefPtr<CefCommandLine> cmd);

//启用录音
DLLEXPORT void TEXPORTS FBroHsCommandLine_EnableSpeechInput(CefRefPtr<CefCommandLine> cmd);

//启用自动播放
DLLEXPORT void TEXPORTS FBroHsCommandLine_EnableAutoplayPoliey(CefRefPtr<CefCommandLine> cmd);

//启用无头模式
DLLEXPORT void TEXPORTS FBroHsCommandLine_EnableHeadless(CefRefPtr<CefCommandLine> cmd);

//设置远程调试端口
DLLEXPORT void TEXPORTS FBroHsCommandLine_SetRemoteDebuggingPort(CefRefPtr<CefCommandLine> cmd, int port);

//禁用GPU
DLLEXPORT void TEXPORTS FBroHsCommandLine_DisableGpu(CefRefPtr<CefCommandLine> cmd);

//禁用GPU缓存
DLLEXPORT void TEXPORTS FBroHsCommandLine_DisableGpuCache(CefRefPtr<CefCommandLine> cmd);

//忽略GPU禁用清单
DLLEXPORT void TEXPORTS FBroHsCommandLine_DisableGpuBlockList(CefRefPtr<CefCommandLine> cmd);



//禁用代理
DLLEXPORT void TEXPORTS FBroHsCommandLine_DisableProxy(CefRefPtr<CefCommandLine> cmd);

#endif // _FBROELIB

//设置全局代理
DLLEXPORT void TEXPORTS FBroHsCommandLine_SetProxy(CefRefPtr<CefCommandLine> cmd, const CefString& url, const CefString& user, const CefString& password);

#endif