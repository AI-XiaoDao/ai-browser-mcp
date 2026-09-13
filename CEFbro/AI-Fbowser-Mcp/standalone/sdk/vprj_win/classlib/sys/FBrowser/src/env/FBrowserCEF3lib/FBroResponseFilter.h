#pragma once
#ifndef FBROWSER_RESPONSEFILTER_H_
#define FBROWSER_RESPONSEFILTER_H_

#include "FBroHsBaseEvent.h"

class FBroHsResponseFilter;

typedef void(CALLBACK* GetFilter_callback)(int, char*, void*, int,bool);
typedef int (CALLBACK* EditFilter_callback)(int, char*, void*, int, int&, void*, int, int&,bool);


class FBroResponseFilter : public CefResponseFilter,public FBroHsEventModel<FBroHsResponseFilter>
{
public:
	FBroResponseFilter();
	FBroResponseFilter(int type, int flag, const CefString& url, HANDLE callpack);
	FBroResponseFilter(FBroHsResponseFilter* hsfilter);
	FBroResponseFilter(CefRefPtr<FBroHsResponseFilter> hsfilter);
	~FBroResponseFilter();

	void Start();
	void End();

private:
	int m_type = 0;
	int m_flag = 0;
	CefString m_url = "";
	GetFilter_callback m_GetFilter = NULL;
	EditFilter_callback m_EditFilter = NULL;

public:

	virtual bool InitFilter()override;

	virtual FilterStatus Filter(void* data_in,
		size_t data_in_size,
		size_t& data_in_read,
		void* data_out,
		size_t data_out_size,
		size_t& data_out_written) override;

protected:
	IMPLEMENT_REFCOUNTING(FBroResponseFilter);
};

//DLLEXPORT CefRefPtr<FBroResponseFilter> TEXPORTS FBroHsResponseFilter_CreateStatic(FBroHsResponseFilter* hsrequesthandler);
DLLEXPORT CefRefPtr<FBroResponseFilter> TEXPORTS FBroHsResponseFilter_Create(CefRefPtr<FBroHsResponseFilter> hsrequesthandler);


class FBroResponseFilterSetData : public virtual CefBaseRefCounted {
public:
	FBroResponseFilterSetData() = default;
	~FBroResponseFilterSetData() = default;
public:
	void Creat(int type, int flag, const CefString& url, HANDLE callpack) {
		responseFilter_ = new FBroResponseFilter(type, flag, url, callpack);
	}
	CefRefPtr<FBroResponseFilter> responseFilter_ = nullptr;

protected:
	IMPLEMENT_REFCOUNTING(FBroResponseFilterSetData);
};

DLLEXPORT void TEXPORTS FBroResponseFilterSetData_Creat(FBroResponseFilterSetData* data, int type, int flag, const char* url, HANDLE callpack);



#endif