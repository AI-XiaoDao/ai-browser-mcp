#pragma once

#include <Windows.h>
#include <string>
#include "pch.h"


namespace FBroDump
{
	typedef int (CALLBACK* OnDump_callback_toE)(const char*, void*);
	typedef int (CALLBACK* OnDump_callback_toHS)(const wchar_t *, void*);

	class Dump
	{
	public:
		Dump() = default;

		Dump(const CefString& filePath, OnDump_callback_toE callback = nullptr);
		Dump(const CefString& filePath, OnDump_callback_toHS callback = nullptr);
		~Dump();

	private:
		static long __stdcall UnhandleExceptionFilter(_EXCEPTION_POINTERS* ExceptionInfo);
	};
}

extern FBroDump::Dump g_dmp;


