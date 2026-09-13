#pragma once

#include "include/base/cef_callback.h"

class CefOnceClosureTask : public CefTask {
public:
	explicit CefOnceClosureTask(base::OnceClosure closure)
		: closure_(std::move(closure)) {}


	// CefTask method
	void Execute() override { std::move(closure_).Run(); }

private:
	base::OnceClosure closure_;

	IMPLEMENT_REFCOUNTING(CefOnceClosureTask);
};


class CefRepeatingClosureTask : public CefTask {
public:
	explicit CefRepeatingClosureTask(const base::RepeatingClosure& closure)
		: closure_(closure) {}


	// CefTask method
	void Execute() override {
		closure_.Run();
		closure_.Reset();
	}

private:
	base::RepeatingClosure closure_;

	IMPLEMENT_REFCOUNTING(CefRepeatingClosureTask);
};

