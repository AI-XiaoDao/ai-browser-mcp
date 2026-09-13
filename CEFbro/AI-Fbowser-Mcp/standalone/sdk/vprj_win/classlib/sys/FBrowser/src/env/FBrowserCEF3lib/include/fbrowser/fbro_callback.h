#ifndef CEF_INCLUDE_FBRO_CALLBACK_H_
#define CEF_INCLUDE_FBRO_CALLBACK_H_

#include "include/cef_base.h"

///
/// Generic callback interface used for asynchronous continuation.
///
/*--cef(source=library)--*/
class FBroClearCacheCallback : public virtual CefBaseRefCounted {
 public:
  virtual void DoFinish(bool success) = 0;
};

#endif
