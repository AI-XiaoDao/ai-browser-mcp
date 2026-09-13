#pragma once
#ifndef FBROWSER_TASKRUNNER_H_
#define FBROWSER_TASKRUNNER_H_


#include "FBroHsBaseEvent.h"

class FBroHsTask;
typedef void (CALLBACK* TaskExecute)(int);

//CefPostTask(TID_UI, new CefClosureTask(base::Bind(&FBroApp::OnBrowserDestroyed, this,browser)));例子,还不知道这么写可对
class FBroTask :public CefTask, public FBroHsEventModel<FBroHsTask>
{
public:
	FBroTask(HANDLE callback, int flag);
	FBroTask(CefRefPtr<FBroHsTask> hscallback);
	FBroTask(FBroHsTask* hscallback);
	~FBroTask();

public:

	virtual void Execute()override;
private:
	TaskExecute m_Execute = NULL;
	int m_flag = 0;
private:
	IMPLEMENT_REFCOUNTING(FBroTask);
};


#ifndef _FBROELIB

DLLEXPORT CefRefPtr<CefTaskRunner> TEXPORTS FBroHsTaskRunner_GetForCurrentThread();
DLLEXPORT CefRefPtr<CefTaskRunner> TEXPORTS FBroHsTaskRunner_GetForThread(int threadId);

//DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_CefPostTaskStatic(int threadId, FBroHsTask* callback);
DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_CefPostTask(int threadId, CefRefPtr<FBroHsTask> callback);

//DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_CefPostDelayedTaskStatic(int threadId, FBroHsTask* callback, int64_t delay_ms);
DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_CefPostDelayedTask(int threadId, CefRefPtr<FBroHsTask> callback, int64_t delay_ms);

DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_IsSame(CefRefPtr<CefTaskRunner> Object, CefRefPtr<CefTaskRunner> that);
DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_BelongsToCurrentThread(CefRefPtr<CefTaskRunner> Object);
DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_BelongsToThread(CefRefPtr<CefTaskRunner> Object, int threadId);

//DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_PostTaskStatic(CefRefPtr<CefTaskRunner> Object, FBroHsTask* callback);
DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_PostTask(CefRefPtr<CefTaskRunner> Object, CefRefPtr<FBroHsTask> callback);

//DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_PostDelayedTaskStatic(CefRefPtr<CefTaskRunner> Object, int64_t delay_ms, FBroHsTask* callback);
DLLEXPORT BOOL TEXPORTS FBroHsTaskRunner_PostDelayedTask(CefRefPtr<CefTaskRunner> Object, int64_t delay_ms, CefRefPtr<FBroHsTask> callback);

#endif // _FBROELIB




#endif