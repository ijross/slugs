# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

import logging





def index():
    """
    This is the main page of the wiki.  
    You will find the title of the requested page in request.args(0).
    If this is None, then just serve the latest revision of something titled "Main page" or something 
    like that. 
    """
    title = request.args(0) or 'Welcome to SlugWiki' 
    content = ' ' 
    form = None
    # You have to serve to the user the most recent revision of the 
    # page with title equal to title.
    
    # Let's uppernice the title.  The last 'title()' below
    # is actually a Python function, if you are wondering.

    button = None 
    rev_button = None

    if title:
        
        #format title for HTML
        display_title = title.title()
     
        title = title.lower()
        row = db(db.pagetable.title == title).select().first()

        #row exists, look it up in the revision table 
        if row is not None:
            rev = db(db.revision.pageref == row.id).select(orderby=~db.revision.date_created).first()
             
            #row exists so produce the button to edit the pos t
            button = A('Edit', _class='btn', _href=URL('default', 'index',args = [title],vars=dict(edit='true')))
            rev_button = A('Revision History', _class='btn', _href=URL('default',
'index', args = [title], vars=dict(revision='true')))
 
        #row does not exist so ask the user to create it 
        else:
            button = A('Create Page', _class='btn', _href=URL('default', 'index',args = [title],vars=dict(edit='true')))
     
        s = rev.body if row is not None else ''
        revising = request.vars.revision == 'true'

        #check to see if the user is editing the page 
        editing = request.vars.edit == 'true'
        
        if editing:
           
            #produce editing form 
            form = SQLFORM.factory(Field('body', 'text',
                                 label='Content',
                                 default= s
                                 ), Field('comment','text'))

            form.add_button('Cancel', URL('default', 'index'))
	       
            if form.process().accepted:
 
                #this is a new page, insert into tables 
                if row is None:
                         
                    page_id = db.pagetable.insert(title=title)
                    db.revision.insert(pageref=page_id, body=form.vars.body,
                                       date_created = datetime.now(),
                                       change_notes=form.vars.comment)
                else: 
                     db.revision.insert(pageref=row.id,body=form.vars.body,
                                       date_created = datetime.now(),
                                      change_notes=form.vars.comment)

                redirect(URL('default','index', args=[title]))

            content = form
        elif revising:
           start_idx = 1
           form = SQLFORM.grid(db.revision.pageref == row.id, args=request.args[:start_idx], details = False, deletable= False, editable=False, 
                 fields=[db.revision.editor,db.revision.date_created,db.revision.change_notes])
           content = form

        else:
            content = s 
    else:
       content = "Search for your favorite subject"

    return dict(display_title=display_title, content=content,editing=editing,button=button,rev_button=rev_button, revising=revising)


def test():
    """This controller is here for testing purposes only.
    Feel free to leave it in, but don't make it part of your wiki.
    """
    title = "This is the wiki's test page"
    form = None
    content = None
    
    # Let's uppernice the title.  The last 'title()' below
    # is actually a Python function, if you are wondering.
    display_title = title.title()
    
    # Gets the body s of the page.
    r = db.testpage(1)
    s = r.body if r is not None else ''
    # Are we editing?
    editing = request.vars.edit == 'true'
    # This is how you can use logging, very useful.
    logger.info("This is a request for page %r, with editing %r" %
                 (title, editing))
    if editing:
        # We are editing.  Gets the body s of the page.
        # Creates a form to edit the content s, with s as default.
        form = SQLFORM.factory(Field('body', 'text',
                                     label='Content',
                                     default=s
                                     ))
        # You can easily add extra buttons to forms.
        form.add_button('Cancel', URL('default', 'test'))
        # Processes the form.
        if form.process().accepted:
            # Writes the new content.
            if r is None:
                # First time: we need to insert it.
                db.testpage.insert(id=1, body=form.vars.body)
            else:
                # We update it.
                r.update_record(body=form.vars.body)
            # We redirect here, so we get this page with GET rather than POST,
            # and we go out of edit mode.
            redirect(URL('default', 'test'))
        content = form
    else:
        # We are just displaying the page
        content = s
    return dict(display_title=display_title, content=content, editing=editing)


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login() 
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)
