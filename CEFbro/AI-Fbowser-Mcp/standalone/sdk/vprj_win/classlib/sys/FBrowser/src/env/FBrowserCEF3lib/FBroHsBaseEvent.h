#pragma once
#ifndef FBROWSER_HS_BASE_EVENT_H_
#define FBROWSER_HS_BASE_EVENT_H_


#include "pch.h"
#include "FBroHsEvent.h"
#include "FBroVersionControl.h"

enum HsEventType
{
	//事件错误
	event_error = 0,
	//静态事件
	event_static,
	//动态事件
	event_ref
};

class FBroHsEventModelBase {
public:
	virtual bool HsEventIsNULL() = 0;
	virtual	void ClearHsEvent() = 0;
};

//DLLEXPORT void TEXPORTS FBroMallocManger_InsertStaticList(FBroHsEventModelBase* fbro_ptr, void* hs_ptr);
//DLLEXPORT void TEXPORTS FBroMallocManger_DeleteStaticList(FBroHsEventModelBase* fbro_ptr);
//DLLEXPORT void TEXPORTS FBroMallocManger_EditStaticList(FBroHsEventModelBase* fbro_ptr, void* hs_ptr);
//DLLEXPORT void TEXPORTS FBroMallocManger_SetHsNullStaticList(void* hs_ptr);


DLLEXPORT void* TEXPORTS FBroMallocManger_New(size_t size);
DLLEXPORT void TEXPORTS FBroMallocManger_Free(void* ptr);
//DLLEXPORT bool TEXPORTS FBroMallocManger_Find(void* ptr);



template<typename T>
class FBroHsEventModel :public FBroHsEventModelBase
{
protected:
	//动态智能指针
	CefRefPtr<T> hs_ref_event_ = nullptr;

	//普通指针,在火山中必须是全局变量
	//T* hs_static_event_ = nullptr;

	//当前类型，0为静态，1为动态智能指针
	//HsEventType type = event_error;
public:
	FBroHsEventModel() {};

	void SetHsEvent(CefRefPtr<T> event) {
		if (event) {
			hs_ref_event_ = event;
			//type = event_ref;
		}
	};

	//void SetHsEvent(T* event) {
	//	if (event) {
	//		hs_static_event_ = event;
	//		type = event_static;
	//	}
	//};

	FBroHsEventModel(CefRefPtr<T> event) {
		SetHsEvent(event);
	};

	//FBroHsEventModel(T* event) {
	//	SetHsEvent(event);
	//};

	~FBroHsEventModel() {
		ClearHsEvent();
	};



	CefRefPtr<T> GetHsEvent() {
		return hs_ref_event_;
	};

	bool HsEventIsNULL() override {
		return !(hs_ref_event_ && hs_ref_event_.get());
		//if (type == event_static && hs_static_event_)
		//	return false;
		//else if (type == event_ref && hs_ref_event_ && hs_ref_event_.get())
		//	return false;
		//else
		//	return true;
	};

	void ClearHsEvent() override {
		if (hs_ref_event_) {
			hs_ref_event_ = nullptr;
		}
		//if (hs_static_event_)
		//	hs_static_event_ = nullptr;
	};


	//HsEventType GetType() {
	//	return type;
	//}
};

#endif