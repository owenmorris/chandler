///////////////////////////////////////////////////////////////////////////////
// Name:        wx/cocoa/NSTableDataSource.h
// Purpose:     wxCocoaNSTableDataSource Objective-C class
// Author:      David Elliott
// Modified by:
// Created:     2003/08/05
// RCS-ID:      $Id: NSTableDataSource.h,v 1.3 2004/05/23 20:50:42 JS Exp $
// Copyright:   (c) 2003 David Elliott
// Licence:     wxWindows licence
///////////////////////////////////////////////////////////////////////////////

#ifndef __WX_COCOA_NSTABLEDATASOURCE_H__
#define __WX_COCOA_NSTABLEDATASOURCE_H__

#import <Foundation/NSObject.h>

// ============================================================================
// @class wxCocoaNSTableDataSource
// ============================================================================
@interface wxCocoaNSTableDataSource : NSObject
{
}

// NSTableDataSource is a loosely defined protocol consisting of the
// following two message implementations
- (int)numberOfRowsInTableView: (NSTableView *)tableView;
- (id)tableView:(NSTableView *)tableView
    objectValueForTableColumn: (NSTableColumn *)tableColumn
    row: (int)rowIndex;
@end // wxCocoaNSTableDataSource

#endif // _WX_COCOA_NSTABLEDATASOURCE_H_
