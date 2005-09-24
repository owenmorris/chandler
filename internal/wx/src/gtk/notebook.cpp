/////////////////////////////////////////////////////////////////////////////
// Name:        notebook.cpp
// Purpose:
// Author:      Robert Roebling
// Id:          $Id: notebook.cpp,v 1.121 2005/09/23 12:53:40 MR Exp $
// Copyright:   (c) 1998 Robert Roebling, Vadim Zeitlin
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

// For compilers that support precompilation, includes "wx.h".
#include "wx/wxprec.h"

#include "wx/notebook.h"

#if wxUSE_NOTEBOOK

#include "wx/panel.h"
#include "wx/utils.h"
#include "wx/imaglist.h"
#include "wx/intl.h"
#include "wx/log.h"
#include "wx/bitmap.h"
#include "wx/fontutil.h"

#include "wx/gtk/private.h"
#include "wx/gtk/win_gtk.h"

#include <gdk/gdkkeysyms.h>

#include "wx/msgdlg.h"

// ----------------------------------------------------------------------------
// events
// ----------------------------------------------------------------------------

DEFINE_EVENT_TYPE(wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGED)
DEFINE_EVENT_TYPE(wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGING)

//-----------------------------------------------------------------------------
// idle system
//-----------------------------------------------------------------------------

extern void wxapp_install_idle_handler();
extern bool g_isIdle;

//-----------------------------------------------------------------------------
// data
//-----------------------------------------------------------------------------

extern bool g_blockEventsOnDrag;

//-----------------------------------------------------------------------------
// wxGtkNotebookPage
//-----------------------------------------------------------------------------

// VZ: this is rather ugly as we keep the pages themselves in an array (it
//     allows us to have quite a few functions implemented in the base class)
//     but the page data is kept in a separate list, so we must maintain them
//     in sync manually... of course, the list had been there before the base
//     class which explains it but it still would be nice to do something
//     about this one day

class wxGtkNotebookPage: public wxObject
{
public:
    wxGtkNotebookPage()
    {
        m_image = -1;
        m_page = (GtkNotebookPage *) NULL;
        m_box = (GtkWidget *) NULL;
    }

    wxString           m_text;
    int                m_image;
    GtkNotebookPage   *m_page;
    GtkLabel          *m_label;
    GtkWidget         *m_box;     // in which the label and image are packed
};


#include "wx/listimpl.cpp"
WX_DEFINE_LIST(wxGtkNotebookPagesList);


//-----------------------------------------------------------------------------
// "switch_page"
//-----------------------------------------------------------------------------

extern "C" {
static void gtk_notebook_page_change_callback(GtkNotebook *WXUNUSED(widget),
                                              GtkNotebookPage *WXUNUSED(page),
                                              gint page,
                                              wxNotebook *notebook )
{
    // are you trying to call SetSelection() from a notebook event handler?
    // you shouldn't!
    wxCHECK_RET( !notebook->m_inSwitchPage,
                 _T("gtk_notebook_page_change_callback reentered") );

    notebook->m_inSwitchPage = TRUE;
    if (g_isIdle)
        wxapp_install_idle_handler();

    int old = notebook->GetSelection();

    wxNotebookEvent eventChanging( wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGING,
                                   notebook->GetId(), page, old );
    eventChanging.SetEventObject( notebook );

    if ( (notebook->GetEventHandler()->ProcessEvent(eventChanging)) &&
         !eventChanging.IsAllowed() )
    {
        /* program doesn't allow the page change */
        gtk_signal_emit_stop_by_name( GTK_OBJECT(notebook->m_widget),
                                      "switch_page" );
    }
    else // change allowed
    {
        // make wxNotebook::GetSelection() return the correct (i.e. consistent
        // with wxNotebookEvent::GetSelection()) value even though the page is
        // not really changed in GTK+
        notebook->m_selection = page;

        wxNotebookEvent eventChanged( wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGED,
                                      notebook->GetId(), page, old );
        eventChanged.SetEventObject( notebook );
        notebook->GetEventHandler()->ProcessEvent( eventChanged );
    }

    notebook->m_inSwitchPage = FALSE;
}
}

//-----------------------------------------------------------------------------
// "size_allocate"
//-----------------------------------------------------------------------------

extern "C" {
static void gtk_page_size_callback( GtkWidget *WXUNUSED(widget), GtkAllocation* alloc, wxWindow *win )
{
    if (g_isIdle)
        wxapp_install_idle_handler();

    if ((win->m_x == alloc->x) &&
        (win->m_y == alloc->y) &&
        (win->m_width == alloc->width) &&
        (win->m_height == alloc->height))
    {
        return;
    }

    win->SetSize( alloc->x, alloc->y, alloc->width, alloc->height );

    /* GTK 1.2 up to version 1.2.5 is broken so that we have to call allocate
       here in order to make repositioning after resizing to take effect. */
    if ((gtk_major_version == 1) &&
        (gtk_minor_version == 2) &&
        (gtk_micro_version < 6) &&
        (win->m_wxwindow) &&
        (GTK_WIDGET_REALIZED(win->m_wxwindow)))
    {
        gtk_widget_size_allocate( win->m_wxwindow, alloc );
    }
}
}

//-----------------------------------------------------------------------------
// "realize" from m_widget
//-----------------------------------------------------------------------------

extern "C" {
static gint
gtk_notebook_realized_callback( GtkWidget * WXUNUSED(widget), wxWindow *win )
{
    if (g_isIdle)
        wxapp_install_idle_handler();

    /* GTK 1.2 up to version 1.2.5 is broken so that we have to call a queue_resize
       here in order to make repositioning before showing to take effect. */
    gtk_widget_queue_resize( win->m_widget );

    return FALSE;
}
}

//-----------------------------------------------------------------------------
// "key_press_event"
//-----------------------------------------------------------------------------

extern "C" {
static gint gtk_notebook_key_press_callback( GtkWidget *widget, GdkEventKey *gdk_event, wxNotebook *notebook )
{
    if (g_isIdle)
        wxapp_install_idle_handler();

    if (!notebook->m_hasVMT) return FALSE;
    if (g_blockEventsOnDrag) return FALSE;

    /* win is a control: tab can be propagated up */
    if ((gdk_event->keyval == GDK_Left) || (gdk_event->keyval == GDK_Right))
    {
        int page;
        int nMax = notebook->GetPageCount();
        if ( nMax-- ) // decrement it to get the last valid index
        {
            int nSel = notebook->GetSelection();

            // change selection wrapping if it becomes invalid
            page = (gdk_event->keyval != GDK_Left) ? nSel == nMax ? 0
                                       : nSel + 1
                        : nSel == 0 ? nMax
                                    : nSel - 1;
        }
        else // notebook is empty, no next page
        {
            return FALSE;
        }

        // m_selection = page;
        gtk_notebook_set_page( GTK_NOTEBOOK(widget), page );

        gtk_signal_emit_stop_by_name( GTK_OBJECT(widget), "key_press_event" );
        return TRUE;
    }

    /* win is a control: tab can be propagated up */
    if ((gdk_event->keyval == GDK_Tab) || (gdk_event->keyval == GDK_ISO_Left_Tab))
    {
        int sel = notebook->GetSelection();
        if (sel == -1)
            return TRUE;
        wxGtkNotebookPage *nb_page = notebook->GetNotebookPage(sel);
        wxCHECK_MSG( nb_page, FALSE, _T("invalid selection in wxNotebook") );

        wxNavigationKeyEvent event;
        event.SetEventObject( notebook );
        /* GDK reports GDK_ISO_Left_Tab for SHIFT-TAB */
        event.SetDirection( (gdk_event->keyval == GDK_Tab) );
        /* CTRL-TAB changes the (parent) window, i.e. switch notebook page */
        event.SetWindowChange( (gdk_event->state & GDK_CONTROL_MASK) ||
                               (gdk_event->keyval == GDK_Left) || (gdk_event->keyval == GDK_Right) );
        event.SetCurrentFocus( notebook );

        wxNotebookPage *client = notebook->GetPage(sel);
        if ( !client->GetEventHandler()->ProcessEvent( event ) )
        {
             client->SetFocus();
        }

        gtk_signal_emit_stop_by_name( GTK_OBJECT(widget), "key_press_event" );
        return TRUE;
    }

    return FALSE;
}
}

//-----------------------------------------------------------------------------
// InsertChild callback for wxNotebook
//-----------------------------------------------------------------------------

static void wxInsertChildInNotebook( wxNotebook* parent, wxWindow* child )
{
    // Hack Alert! (Part I): This sets the notebook as the parent of the child
    // widget, and takes care of some details such as updating the state and
    // style of the child to reflect its new location.  We do this early
    // because without it GetBestSize (which is used to set the initial size
    // of controls if an explicit size is not given) will often report
    // incorrect sizes since the widget's style context is not fully known.
    // See bug #901694 for details
    // (http://sourceforge.net/tracker/?func=detail&aid=901694&group_id=9863&atid=109863)
    gtk_widget_set_parent(child->m_widget, parent->m_widget);

    // NOTE: This should be considered a temporary workaround until we can
    // work out the details and implement delaying the setting of the initial
    // size of widgets until the size is really needed.
}

//-----------------------------------------------------------------------------
// wxNotebook
//-----------------------------------------------------------------------------

IMPLEMENT_DYNAMIC_CLASS(wxNotebook,wxControl)

BEGIN_EVENT_TABLE(wxNotebook, wxControl)
    EVT_NAVIGATION_KEY(wxNotebook::OnNavigationKey)
END_EVENT_TABLE()

void wxNotebook::Init()
{
    m_padding = 0;
    m_inSwitchPage = FALSE;

    m_imageList = (wxImageList *) NULL;
    m_selection = -1;
    m_themeEnabled = TRUE;
}

wxNotebook::wxNotebook()
{
    Init();
}

wxNotebook::wxNotebook( wxWindow *parent, wxWindowID id,
      const wxPoint& pos, const wxSize& size,
      long style, const wxString& name )
{
    Init();
    Create( parent, id, pos, size, style, name );
}

wxNotebook::~wxNotebook()
{
    DeleteAllPages();
}

bool wxNotebook::Create(wxWindow *parent, wxWindowID id,
                        const wxPoint& pos, const wxSize& size,
                        long style, const wxString& name )
{
    m_needParent = TRUE;
    m_acceptsFocus = TRUE;
    m_insertCallback = (wxInsertChildFunction)wxInsertChildInNotebook;

    if (!PreCreation( parent, pos, size ) ||
        !CreateBase( parent, id, pos, size, style, wxDefaultValidator, name ))
    {
        wxFAIL_MSG( wxT("wxNoteBook creation failed") );
        return FALSE;
    }


    m_widget = gtk_notebook_new();

    gtk_notebook_set_scrollable( GTK_NOTEBOOK(m_widget), 1 );

    gtk_signal_connect( GTK_OBJECT(m_widget), "switch_page",
      GTK_SIGNAL_FUNC(gtk_notebook_page_change_callback), (gpointer)this );

    m_parent->DoAddChild( this );

    if (m_windowStyle & wxNB_RIGHT)
        gtk_notebook_set_tab_pos( GTK_NOTEBOOK(m_widget), GTK_POS_RIGHT );
    if (m_windowStyle & wxNB_LEFT)
        gtk_notebook_set_tab_pos( GTK_NOTEBOOK(m_widget), GTK_POS_LEFT );
    if (m_windowStyle & wxNB_BOTTOM)
        gtk_notebook_set_tab_pos( GTK_NOTEBOOK(m_widget), GTK_POS_BOTTOM );

    gtk_signal_connect( GTK_OBJECT(m_widget), "key_press_event",
      GTK_SIGNAL_FUNC(gtk_notebook_key_press_callback), (gpointer)this );

    PostCreation(size);

    gtk_signal_connect( GTK_OBJECT(m_widget), "realize",
                            GTK_SIGNAL_FUNC(gtk_notebook_realized_callback), (gpointer) this );

    return TRUE;
}

int wxNotebook::GetSelection() const
{
    wxCHECK_MSG( m_widget != NULL, -1, wxT("invalid notebook") );

    if ( m_selection == -1 )
    {
        GList *nb_pages = GTK_NOTEBOOK(m_widget)->children;

        if (g_list_length(nb_pages) != 0)
        {
            GtkNotebook *notebook = GTK_NOTEBOOK(m_widget);

            gpointer cur = notebook->cur_page;
            if ( cur != NULL )
            {
                wxConstCast(this, wxNotebook)->m_selection =
                    g_list_index( nb_pages, cur );
            }
        }
    }

    return m_selection;
}

wxString wxNotebook::GetPageText( size_t page ) const
{
    wxCHECK_MSG( m_widget != NULL, wxT(""), wxT("invalid notebook") );

    wxGtkNotebookPage* nb_page = GetNotebookPage(page);
    if (nb_page)
        return nb_page->m_text;
    else
        return wxT("");
}

int wxNotebook::GetPageImage( size_t page ) const
{
    wxCHECK_MSG( m_widget != NULL, -1, wxT("invalid notebook") );

    wxGtkNotebookPage* nb_page = GetNotebookPage(page);
    if (nb_page)
        return nb_page->m_image;
    else
        return -1;
}

wxGtkNotebookPage* wxNotebook::GetNotebookPage( int page ) const
{
    wxCHECK_MSG( m_widget != NULL, (wxGtkNotebookPage*) NULL, wxT("invalid notebook") );

    wxCHECK_MSG( page < (int)m_pagesData.GetCount(), (wxGtkNotebookPage*) NULL, wxT("invalid notebook index") );

    return m_pagesData.Item(page)->GetData();
}

int wxNotebook::SetSelection( size_t page )
{
    wxCHECK_MSG( m_widget != NULL, -1, wxT("invalid notebook") );

    wxCHECK_MSG( page < m_pagesData.GetCount(), -1, wxT("invalid notebook index") );

    int selOld = GetSelection();

    // cache the selection
    m_selection = page;
    gtk_notebook_set_page( GTK_NOTEBOOK(m_widget), page );

    wxNotebookPage *client = GetPage(page);
    if ( client )
        client->SetFocus();

    return selOld;
}

bool wxNotebook::SetPageText( size_t page, const wxString &text )
{
    wxCHECK_MSG( m_widget != NULL, FALSE, wxT("invalid notebook") );

    wxGtkNotebookPage* nb_page = GetNotebookPage(page);

    wxCHECK_MSG( nb_page, FALSE, wxT("SetPageText: invalid page index") );

    nb_page->m_text = text;

    gtk_label_set( nb_page->m_label, wxGTK_CONV( nb_page->m_text ) );

    return TRUE;
}

bool wxNotebook::SetPageImage( size_t page, int image )
{
    /* HvdH 28-12-98: now it works, but it's a bit of a kludge */

    wxGtkNotebookPage* nb_page = GetNotebookPage(page);

    if (!nb_page) return FALSE;

    /* Optimization posibility: return immediately if image unchanged.
     * Not enabled because it may break existing (stupid) code that
     * manipulates the imagelist to cycle images */

    /* if (image == nb_page->m_image) return TRUE; */

    /* For different cases:
       1) no image -> no image
       2) image -> no image
       3) no image -> image
       4) image -> image */

    if (image == -1 && nb_page->m_image == -1)
        return TRUE; /* Case 1): Nothing to do. */

    GtkWidget *pixmapwid = (GtkWidget*) NULL;

    if (nb_page->m_image != -1)
    {
        /* Case 2) or 4). There is already an image in the gtkhbox. Let's find it */

        GList *child = gtk_container_children(GTK_CONTAINER(nb_page->m_box));
        while (child)
        {
            if (GTK_IS_PIXMAP(child->data))
            {
                pixmapwid = GTK_WIDGET(child->data);
                break;
            }
            child = child->next;
        }

        /* We should have the pixmap widget now */
        wxASSERT(pixmapwid != NULL);

        if (image == -1)
        {
            /* If there's no new widget, just remove the old from the box */
            gtk_container_remove(GTK_CONTAINER(nb_page->m_box), pixmapwid);
            nb_page->m_image = -1;

            return TRUE; /* Case 2) */
        }
    }

    /* Only cases 3) and 4) left */
    wxASSERT( m_imageList != NULL ); /* Just in case */

    /* Construct the new pixmap */
    const wxBitmap *bmp = m_imageList->GetBitmapPtr(image);
    GdkPixmap *pixmap = bmp->GetPixmap();
    GdkBitmap *mask = (GdkBitmap*) NULL;
    if ( bmp->GetMask() )
    {
        mask = bmp->GetMask()->GetBitmap();
    }

    if (pixmapwid == NULL)
    {
        /* Case 3) No old pixmap. Create a new one and prepend it to the hbox */
        pixmapwid = gtk_pixmap_new (pixmap, mask );

        /* CHECKME: Are these pack flags okay? */
        gtk_box_pack_start(GTK_BOX(nb_page->m_box), pixmapwid, FALSE, FALSE, m_padding);
        gtk_widget_show(pixmapwid);
    }
    else
    {
        /* Case 4) Simply replace the pixmap */
        gtk_pixmap_set(GTK_PIXMAP(pixmapwid), pixmap, mask);
    }

    nb_page->m_image = image;

    return TRUE;
}

void wxNotebook::SetPageSize( const wxSize &WXUNUSED(size) )
{
    wxFAIL_MSG( wxT("wxNotebook::SetPageSize not implemented") );
}

void wxNotebook::SetPadding( const wxSize &padding )
{
    wxCHECK_RET( m_widget != NULL, wxT("invalid notebook") );

    m_padding = padding.GetWidth();

    int i;
    for (i=0; i<int(GetPageCount()); i++)
    {
        wxGtkNotebookPage* nb_page = GetNotebookPage(i);
        wxASSERT(nb_page != NULL);

        if (nb_page->m_image != -1)
        {
            // gtk_box_set_child_packing sets padding on BOTH sides
            // icon provides left padding, label provides center and right
            int image = nb_page->m_image;
            SetPageImage(i,-1);
            SetPageImage(i,image);
        }
        wxASSERT(nb_page->m_label);
        gtk_box_set_child_packing(GTK_BOX(nb_page->m_box),
                                  GTK_WIDGET(nb_page->m_label),
                                  FALSE, FALSE, m_padding, GTK_PACK_END);
    }
}

void wxNotebook::SetTabSize(const wxSize& WXUNUSED(sz))
{
    wxFAIL_MSG( wxT("wxNotebook::SetTabSize not implemented") );
}

bool wxNotebook::DeleteAllPages()
{
    wxCHECK_MSG( m_widget != NULL, FALSE, wxT("invalid notebook") );

    while (m_pagesData.GetCount() > 0)
        DeletePage( m_pagesData.GetCount()-1 );

    wxASSERT_MSG( GetPageCount() == 0, _T("all pages must have been deleted") );

    InvalidateBestSize();
    return wxNotebookBase::DeleteAllPages();
}

wxNotebookPage *wxNotebook::DoRemovePage( size_t page )
{
    if ( m_selection != -1 && (size_t)m_selection >= page )
    {
        // the index will become invalid after the page is deleted
        m_selection = -1;
    }

    wxNotebookPage *client = wxNotebookBase::DoRemovePage(page);
    if ( !client )
        return NULL;

    gtk_widget_ref( client->m_widget );
    gtk_widget_unrealize( client->m_widget );
    gtk_widget_unparent( client->m_widget );

    // gtk_notebook_remove_page() sends "switch_page" signal with some strange
    // new page index (when deleting selected page 0, new page is 1 although,
    // clearly, the selection should stay 0), so suppress this
    gtk_signal_disconnect_by_func( GTK_OBJECT(m_widget),
      GTK_SIGNAL_FUNC(gtk_notebook_page_change_callback), (gpointer) this );

    gtk_notebook_remove_page( GTK_NOTEBOOK(m_widget), page );

    gtk_signal_connect( GTK_OBJECT(m_widget), "switch_page",
      GTK_SIGNAL_FUNC(gtk_notebook_page_change_callback), (gpointer)this );

    wxGtkNotebookPage* p = GetNotebookPage(page);
    m_pagesData.DeleteObject(p);
    delete p;

    return client;
}

bool wxNotebook::InsertPage( size_t position,
                             wxNotebookPage* win,
                             const wxString& text,
                             bool select,
                             int imageId )
{
    wxCHECK_MSG( m_widget != NULL, FALSE, wxT("invalid notebook") );

    wxCHECK_MSG( win->GetParent() == this, FALSE,
               wxT("Can't add a page whose parent is not the notebook!") );

    wxCHECK_MSG( position <= GetPageCount(), FALSE,
                 _T("invalid page index in wxNotebookPage::InsertPage()") );

    // Hack Alert! (Part II): See above in wxInsertChildInNotebook callback
    // why this has to be done.  NOTE: using gtk_widget_unparent here does not
    // work as it seems to undo too much and will cause errors in the
    // gtk_notebook_insert_page below, so instead just clear the parent by
    // hand here.
    win->m_widget->parent = NULL;

    // don't receive switch page during addition
    gtk_signal_disconnect_by_func( GTK_OBJECT(m_widget),
      GTK_SIGNAL_FUNC(gtk_notebook_page_change_callback), (gpointer) this );

    if (m_themeEnabled)
        win->SetThemeEnabled(TRUE);

    GtkNotebook *notebook = GTK_NOTEBOOK(m_widget);

    wxGtkNotebookPage *nb_page = new wxGtkNotebookPage();

    if ( position == GetPageCount() )
        m_pagesData.Append( nb_page );
    else
        m_pagesData.Insert( position, nb_page );

    m_pages.Insert(win, position);

    nb_page->m_box = gtk_hbox_new( FALSE, 1 );
    gtk_container_border_width( GTK_CONTAINER(nb_page->m_box), 2 );

    gtk_signal_connect( GTK_OBJECT(win->m_widget), "size_allocate",
      GTK_SIGNAL_FUNC(gtk_page_size_callback), (gpointer)win );

#ifndef __VMS
   // On VMS position is unsigned and thus always positive
   if (position < 0)
        gtk_notebook_append_page( notebook, win->m_widget, nb_page->m_box );
    else
#endif
     gtk_notebook_insert_page( notebook, win->m_widget, nb_page->m_box, position );

    nb_page->m_page = (GtkNotebookPage*) g_list_last(notebook->children)->data;

    /* set the label image */
    nb_page->m_image = imageId;

    if (imageId != -1)
    {
        wxASSERT( m_imageList != NULL );

        const wxBitmap *bmp = m_imageList->GetBitmapPtr(imageId);
        GdkPixmap *pixmap = bmp->GetPixmap();
        GdkBitmap *mask = (GdkBitmap*) NULL;
        if ( bmp->GetMask() )
        {
            mask = bmp->GetMask()->GetBitmap();
        }

        GtkWidget *pixmapwid = gtk_pixmap_new (pixmap, mask );

        gtk_box_pack_start(GTK_BOX(nb_page->m_box), pixmapwid, FALSE, FALSE, m_padding);

        gtk_widget_show(pixmapwid);
    }

    /* set the label text */

    nb_page->m_text = text;
    if (nb_page->m_text.IsEmpty()) nb_page->m_text = wxT("");

    nb_page->m_label = GTK_LABEL( gtk_label_new(wxGTK_CONV(nb_page->m_text)) );
    gtk_box_pack_end( GTK_BOX(nb_page->m_box), GTK_WIDGET(nb_page->m_label), FALSE, FALSE, m_padding );

    /* apply current style */
    GtkRcStyle *style = CreateWidgetStyle();
    if ( style )
    {
        gtk_widget_modify_style(GTK_WIDGET(nb_page->m_label), style);
        gtk_rc_style_unref(style);
    }

    /* show the label */
    gtk_widget_show( GTK_WIDGET(nb_page->m_label) );
    if (select && (m_pagesData.GetCount() > 1))
    {
#ifndef __VMS
   // On VMS position is unsigned and thus always positive
        if (position < 0)
            SetSelection( GetPageCount()-1 );
        else
#endif
            SetSelection( position );
    }

    gtk_signal_connect( GTK_OBJECT(m_widget), "switch_page",
      GTK_SIGNAL_FUNC(gtk_notebook_page_change_callback), (gpointer)this );

    InvalidateBestSize();
    return TRUE;
}

// helper for HitTest(): check if the point lies inside the given widget which
// is the child of the notebook whose position and border size are passed as
// parameters
static bool
IsPointInsideWidget(const wxPoint& pt, GtkWidget *w,
                    gint x, gint y, gint border = 0)
{
    return
        (pt.x >= w->allocation.x - x - border) &&
        (pt.x <= w->allocation.x - x + border + w->allocation.width) &&
        (pt.y >= w->allocation.y - y - border) &&
        (pt.y <= w->allocation.y - y + border + w->allocation.height);
}

int wxNotebook::HitTest(const wxPoint& pt, long *flags) const
{
    const gint x = m_widget->allocation.x;
    const gint y = m_widget->allocation.y;

    const size_t count = GetPageCount();
    for ( size_t i = 0; i < count; i++ )
    {
        wxGtkNotebookPage* nb_page = GetNotebookPage(i);
        GtkWidget *box = nb_page->m_box;

        // VZ: don't know how to find the border width in GTK+ 1.2
#ifdef __WXGTK20__
        const gint border = gtk_container_get_border_width(GTK_CONTAINER(box));
#else // !GTK+ 2.x
        const gint border = 0;
#endif
        if ( IsPointInsideWidget(pt, box, x, y, border) )
        {
            // ok, we're inside this tab -- now find out where, if needed
            if ( flags )
            {
                GtkWidget *pixmap = NULL;

                GList *children = gtk_container_children(GTK_CONTAINER(box));
                for ( GList *child = children; child; child = child->next )
                {
                    if ( GTK_IS_PIXMAP(child->data) )
                    {
                        pixmap = GTK_WIDGET(child->data);
                        break;
                    }
                }

                if ( children )
                    g_list_free(children);

                if ( pixmap && IsPointInsideWidget(pt, pixmap, x, y) )
                {
                    *flags = wxNB_HITTEST_ONICON;
                }
                else if ( IsPointInsideWidget(pt, GTK_WIDGET(nb_page->m_label), x, y) )
                {
                    *flags = wxNB_HITTEST_ONLABEL;
                }
                else
                {
                    *flags = wxNB_HITTEST_ONITEM;
                }
            }

            return i;
        }
    }

    if ( flags )
        *flags = wxNB_HITTEST_NOWHERE;

    return wxNOT_FOUND;
}

void wxNotebook::OnNavigationKey(wxNavigationKeyEvent& event)
{
    if (event.IsWindowChange())
        AdvanceSelection( event.GetDirection() );
    else
        event.Skip();
}

#if wxUSE_CONSTRAINTS

// override these 2 functions to do nothing: everything is done in OnSize
void wxNotebook::SetConstraintSizes( bool WXUNUSED(recurse) )
{
    // don't set the sizes of the pages - their correct size is not yet known
    wxControl::SetConstraintSizes(FALSE);
}

bool wxNotebook::DoPhase( int WXUNUSED(nPhase) )
{
    return TRUE;
}

#endif

void wxNotebook::DoApplyWidgetStyle(GtkRcStyle *style)
{
    gtk_widget_modify_style(m_widget, style);
    size_t cnt = m_pagesData.GetCount();
    for (size_t i = 0; i < cnt; i++)
        gtk_widget_modify_style(GTK_WIDGET(GetNotebookPage(i)->m_label), style);
}

bool wxNotebook::IsOwnGtkWindow( GdkWindow *window )
{
    return ((m_widget->window == window) ||
            (NOTEBOOK_PANEL(m_widget) == window));
}

// static
wxVisualAttributes
wxNotebook::GetClassDefaultAttributes(wxWindowVariant WXUNUSED(variant))
{
    return GetDefaultAttributesFromGTKWidget(gtk_notebook_new);
}

//-----------------------------------------------------------------------------
// wxNotebookEvent
//-----------------------------------------------------------------------------

IMPLEMENT_DYNAMIC_CLASS(wxNotebookEvent, wxNotifyEvent)

#endif
