#pragma once
#ifndef FBROWSER_RESOUTCEHANDLER_H_
#define FBROWSER_RESOUTCEHANDLER_H_

#include "FBroHsBaseEvent.h"

class FBroHsResourceHandler;

class FBroResourceHandler:public CefResourceHandler,public FBroHsEventModel<FBroHsResourceHandler>
{
public:
	FBroResourceHandler(int flag) ;

	FBroResourceHandler(FBroHsResourceHandler* hscallback);
	FBroResourceHandler(CefRefPtr<FBroHsResourceHandler> hscallback);
	
	~FBroResourceHandler();

	void Start();

	/**********************************CefResourceHandler************************************/
	virtual bool Open(CefRefPtr<CefRequest> request,
		bool& handle_request,
		CefRefPtr<CefCallback> callback) override;

	virtual bool ProcessRequest(CefRefPtr<CefRequest> request,
		CefRefPtr<CefCallback> callback) override;

	virtual void GetResponseHeaders(CefRefPtr<CefResponse> response,
		int64_t& response_length,
		CefString& redirectUrl) override;

	virtual bool Skip(int64_t bytes_to_skip,
		int64_t& bytes_skipped,
		CefRefPtr<CefResourceSkipCallback> callback) override;

	virtual bool Read(void* data_out,
		int bytes_to_read,
		int& bytes_read,
		CefRefPtr<CefResourceReadCallback> callback) override;
	virtual void Cancel() override;
	/**********************************CefResourceHandler END************************************/
private:
	int m_flag = 0;
protected:
	IMPLEMENT_REFCOUNTING(FBroResourceHandler);
};

//DLLEXPORT CefRefPtr<FBroResourceHandler> TEXPORTS FBroHsResourceHandler_CreateStatic(FBroHsResourceHandler* hsrequesthandler);
DLLEXPORT CefRefPtr<FBroResourceHandler> TEXPORTS FBroHsResourceHandler_Create(CefRefPtr<FBroHsResourceHandler> hsrequesthandler);

#endif