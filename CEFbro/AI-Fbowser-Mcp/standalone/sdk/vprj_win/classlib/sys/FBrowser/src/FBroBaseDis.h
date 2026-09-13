#pragma once
#ifndef FBROWSER_HS_BASE_DIS_H_
#define FBROWSER_HS_BASE_DIS_H_

#include <mutex>

#include "env\FBrowserCEF3lib\pch.h"
#include "env\FBrowserCEF3lib\FBroApp.h"
#include "env\FBrowserCEF3lib\FBroBase.h"
#include "env\FBrowserCEF3lib\FBroBaseEvent.h"
#include "env\FBrowserCEF3lib\FBroBrowser.h"
#include "env\FBrowserCEF3lib\FBroBrowserHost.h"
#include "env\FBrowserCEF3lib\FBroBrowserListControl.h"
#include "env\FBrowserCEF3lib\FBroCallback.h"
#include "env\FBrowserCEF3lib\FBroClient.h"
#include "env\FBrowserCEF3lib\FBroCommand.h"
#include "env\FBrowserCEF3lib\FBroContextIdData.h"
#include "env\FBrowserCEF3lib\FBroControl.h"
#include "env\FBrowserCEF3lib\FBroCookieManager.h"
#include "env\FBrowserCEF3lib\FBroDictionaryValue.h"
#include "env\FBrowserCEF3lib\FBroDom.h"
#include "env\FBrowserCEF3lib\FBroDownloadItem.h"
#include "env\FBrowserCEF3lib\FBroDragData.h"
#include "env\FBrowserCEF3lib\FBroDump.h"
#include "env\FBrowserCEF3lib\FBroEValueControl.h"
#include "env\FBrowserCEF3lib\FBroFrame.h"
#include "env\FBrowserCEF3lib\FBroFrameTianBiao.h"
#include "env\FBrowserCEF3lib\FBroGlobalInterface.h"
#include "env\FBrowserCEF3lib\FBroHookEvent.h"
#include "env\FBrowserCEF3lib\FBroHsBaseEvent.h"
#include "env\FBrowserCEF3lib\FBroHsEvent.h"
#include "env\FBrowserCEF3lib\FBroImage.h"
#include "env\FBrowserCEF3lib\FBroInit.h"
#include "env\FBrowserCEF3lib\FBroListValue.h"
#include "env\FBrowserCEF3lib\FBroMenuModel.h"
#include "env\FBrowserCEF3lib\FBroOnceClosureTask.h"
#include "env\FBrowserCEF3lib\FBroPostData.h"
#include "env\FBrowserCEF3lib\FBroProcessMessage.h"
#include "env\FBrowserCEF3lib\FBroProxyUserData.h"
#include "env\FBrowserCEF3lib\FBroQueryHandler.h"
#include "env\FBrowserCEF3lib\FBroRequest.h"
#include "env\FBrowserCEF3lib\FBroRequestContext.h"
#include "env\FBrowserCEF3lib\FBroResourceHandler.h"
#include "env\FBrowserCEF3lib\FBroResponse.h"
#include "env\FBrowserCEF3lib\FBroResponseFilter.h"
#include "env\FBrowserCEF3lib\FBroServer.h"
#include "env\FBrowserCEF3lib\FBroServerHandler.h"
#include "env\FBrowserCEF3lib\FBroSetControl.h"
#include "env\FBrowserCEF3lib\FBroSharedMemoryRegion.h"
#include "env\FBrowserCEF3lib\FBroSocket.h"
#include "env\FBrowserCEF3lib\FBroSSLInfo.h"
#include "env\FBrowserCEF3lib\FBroStream.h"
#include "env\FBrowserCEF3lib\FBroSynEventDis.h"
#include "env\FBrowserCEF3lib\FBroTaskRunner.h"
#include "env\FBrowserCEF3lib\FBroTypes.h"
#include "env\FBrowserCEF3lib\FBroUnits.h"
#include "env\FBrowserCEF3lib\FBroV8Context.h"
#include "env\FBrowserCEF3lib\FBroV8Exception.h"
#include "env\FBrowserCEF3lib\FBroV8Stack.h"
#include "env\FBrowserCEF3lib\FBroV8Value.h"
#include "env\FBrowserCEF3lib\FBroValue.h"
#include "env\FBrowserCEF3lib\FBroVersionControl.h"
#include "env\FBrowserCEF3lib\FBroWebSocket.h"
#include "env\FBrowserCEF3lib\FBroWebSocketClient.h"
#include "env\FBrowserCEF3lib\FBroWSSClient.h"
#include "env\FBrowserCEF3lib\FBroX509Certificate.h"
#include "env\FBrowserCEF3lib\FBroX509CertPrincipal.h"

#include "env\FBrowserCEF3lib\FBroString.h"

#include "env\FBrowserCEF3lib\FBroMiddleData.h"
#include "env\FBrowserCEF3lib\FBroHsBaseEvent.h"

#include "env\FBrowserCEF3lib\FBroX509CertPrincipal.h"

#include "env\FBrowserCEF3lib\FBroUseExtraData.h"

#include "env\FBrowserCEF3lib\FBroURLRequest.h"

#include "env\FBrowserCEF3lib\FBroVersion.h"

#include "env\FBrowserCEF3lib\FBroVIPStruct.h"
#include "env\FBrowserCEF3lib\FBroVIPControl.h"

//#include "env\FBrowserCEF3lib\FBroVIPEvent.h"
#include "env\FBrowserCEF3lib\FBroVIPUserAgentData.h"
#include "env\FBrowserCEF3lib\FBroVIPEventInterface.h"
#include "env\FBrowserCEF3lib\FBroVIPInterface.h"


class FBroUnit {
public:
	static int UnicodeToAnsi(const wchar_t* szStr, char* pResult, int insize) {
		if (insize <= 0) {
			return WideCharToMultiByte(CP_ACP, 0, szStr, -1, NULL, 0, NULL, NULL);
		}
		else {
			return WideCharToMultiByte(CP_ACP, 0, szStr, -1, pResult, insize, NULL, NULL);
		}
	}

	//只能内部使用
	static std::string UnicodeToString(CWString hs_str) {
		int size = WideCharToMultiByte(CP_ACP, 0, hs_str.GetText(), -1, NULL, 0, NULL, NULL);
		std::unique_ptr<char[]> temp = std::make_unique<char[]>(size + 1);
		WideCharToMultiByte(CP_ACP, 0, hs_str.GetText(), -1, temp.get(), size, NULL, NULL);
		return std::string(temp.get());
	}

	static char* UnicodeToAnsi(const wchar_t* szStr)//使用后需释放
	{
		int nLen = WideCharToMultiByte(CP_ACP, 0, szStr, -1, NULL, 0, NULL, NULL);
		if (nLen <= 0) return NULL;
		char* pResult = new char[nLen] {'\0'};
		WideCharToMultiByte(CP_ACP, 0, szStr, -1, pResult, nLen, NULL, NULL);
		return pResult;
	}

	static void FreeCharArray(char*& p) noexcept {
		if (p) {
			delete[] p;
			p = nullptr;
		}
	}

	static std::unique_ptr<char[]> UnicodeToAnsiUnique(const wchar_t* szStr) {
		if (!szStr) return nullptr;
		int nLen = WideCharToMultiByte(CP_ACP, 0, szStr, -1, NULL, 0, NULL, NULL);
		if (nLen <= 0) return nullptr;
		std::unique_ptr<char[]> pResult = std::make_unique<char[]>(nLen);
		WideCharToMultiByte(CP_ACP, 0, szStr, -1, pResult.get(), nLen, NULL, NULL);
		return pResult;
	}

	static CWString ToCWString(const char* lpSrcBuffer) {
		int size = (int)strlen(lpSrcBuffer);
		if (size <= 0) return CWString();
		int nDestLength = MultiByteToWideChar(CP_ACP, NULL, lpSrcBuffer, size, NULL, NULL);
		std::unique_ptr<wchar_t[]> lpwszDestBuffer = std::make_unique<wchar_t[]>(nDestLength + 1);
		MultiByteToWideChar(CP_ACP, NULL, lpSrcBuffer, size, lpwszDestBuffer.get(), nDestLength);
		return CVolString(lpwszDestBuffer.get());
	}

	static CWString FBroStringToCWString(CefRefPtr<FBroString> data) {
		int size = FBroString_WSize(data);
		if (size <= 0) return CWString();
		std::unique_ptr<wchar_t[]> buf = std::make_unique<wchar_t[]>(size + 1);
		FBroString_GetWcharData(data, buf.get());
		return CVolString(buf.get());
	}

	//使用后记得要释放
	static void  CopyFBroData(E_COOKIEDATA indata, POINT_COOKIEDATA retdata) {

		if (!retdata) return;

		if (indata.name) {
			int size = (int)strlen(indata.name);
			retdata->name = new char[size + 1] {'\0'};
			memcpy_s(retdata->name, size, indata.name, size);
			//retdata->name[size] = '\0';
		}
		if (indata.value) {
			int size = (int)strlen(indata.value);
			retdata->value = new char[size + 1] {'\0'};
			memcpy_s(retdata->value, size, indata.value, size);
			//retdata->value[size] = '\0';
		}
		if (indata.domain) {
			int size = (int)strlen(indata.domain);
			retdata->domain = new char[size + 1] {'\0'};
			memcpy_s(retdata->domain, size, indata.domain, size);
			//retdata->domain[size] = '\0';
		}
		if (indata.path) {
			int size = (int)strlen(indata.path);
			retdata->path = new char[size + 1] {'\0'};
			memcpy_s(retdata->path, size, indata.path, size);
			//retdata->path[size] = '\0';
		}
		retdata->httponly = indata.httponly;
		retdata->has_expires = indata.has_expires;

		retdata->expires_time = indata.expires_time;
		retdata->last_access_time = indata.last_access_time;

		retdata->secure = indata.secure;
		retdata->same_site = indata.same_site;
		retdata->priority = indata.priority;
	}


	//照搬火山源码
	static CWString StringToCWString(char* strdata) {
		CVolMem memBuf(CVolMem((void*)strdata, strlen(strdata)));
		memBuf.AddDWord(0);
		return CWString(memBuf.GetTextPtr());
	}

	//延时，不卡事件，精益延时移植而来
	static void WaitUserTimer(int waitTime) {
		if (waitTime <= 0) return;
		HANDLE handle = ::CreateWaitableTimerA(NULL, false, NULL);
		LARGE_INTEGER time;
		time.QuadPart = -10 * waitTime * 1000;
		SetWaitableTimer(handle, &time, NULL, NULL, NULL, false);

		while (MsgWaitForMultipleObjects(1, &handle, FALSE, -1, QS_ALLPOSTMESSAGE) != 0) {
			MSG msg;
			while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) { //处理事件
				TranslateMessage(&msg);
				DispatchMessage(&msg);
			}
		}
		::CloseHandle(handle);
	}


};

#ifdef _DEBUG 

class FBroDebugMessage {
public:

	static bool* GetClose() {
		static bool is_close_ = true;
		return &is_close_;
	}

	static void CloseMessage(bool close) {

		*GetClose() = close;
	}

	//显示类初始化和释放相关信息
	static void ShowClassType(CVolString class_name, int type, CVolObject* class_ptr) {
		//空的数据没必要显示，这个是火山内置判断是不是空的，实际这个类是存在的
		// 20240312发现火山是否为空存在问题，勾析函数内获取不到，暂时屏蔽
		//if (class_ptr && class_ptr->IsNullObject())
		//    return;

		if (*GetClose())
			return;

		CVolString a(_T("【FBrowser类监测】") + class_name);
		CVolString b(type == 0 ? _T("初始化") : _T("清理释放"));
		CVolString c(_T("类指针:") + CVolString((INT_P)class_ptr));
		// CVolString d(_T("是否动态类:") + CVolString(is_new ? _T("真") : _T("假")));
		_DEBUG_STATMENT(DebugTrace(FALSE, 0, 0, _T("SSS"), a.GetText(), b.GetText(), c.GetText()));
	}

	//显示类初始化和释放相关信息
	static void ShowError(CVolString class_name, CVolString fun_name, CVolString error) {

		CVolString a(_T("【FBrowser异常监测】") + class_name);
		CVolString b(fun_name);
		CVolString c(_T("错误:") + error);
		_DEBUG_STATMENT(DebugTrace(FALSE, 0, 0, _T("SSS"), a.GetText(), b.GetText(), c.GetText()));
	}

};

#define _FBRO_CHECK_EVENT_TYPE(basee_vent,type,class_name,fun_name) if (basee_vent && basee_vent->type_ != type) { FBroDebugMessage::ShowError(class_name,fun_name,_T("设置事件格式错误，请核查，程序已退出！！！")); exit(0); };
#define _FBRO_SHOW_CLASS_TYPE(class_name,type) FBroDebugMessage::ShowClassType(class_name,type,this);
#else
#define _FBRO_CHECK_EVENT_TYPE(basee_vent,type,class_name,fun_name) 
#define _FBRO_SHOW_CLASS_TYPE(class_name,type)
#endif 


#define _FBRO_NEW_DELETE_OVERRIDE()             \
public:                                         \
	void* operator new(size_t size) {           \
		return FBroMallocManger_New(size);      \
	}                                           \
	void operator delete(void* ptr) {           \
		FBroMallocManger_Free(ptr);             \
    }                                           \



#endif