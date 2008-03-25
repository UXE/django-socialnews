from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from helpers import *
import bforms
import logging
import simplejson
from django.template.loader import get_template
from django.template import Context

@login_required
def link_submit(request, topic_name):
    topic = get_topic(request, topic_name)
    if request.method == 'GET':
        form = bforms.NewLink(user = request.user, topic = topic)
    if request.method == 'POST':
        form = bforms.NewLink( user = request.user, topic = topic, data = request.POST)
        if form.is_valid():
            link = form.save()
            return HttpResponseRedirect(link.get_absolute_url())
    payload = {'topic':topic,'form':form}
    return render(request, payload, 'news/create_link.html')

def link_details(request, topic_name, link_id):
    topic = get_topic(request, topic_name)
    if request.user.is_authenticated():
        link = Link.objects.get_query_set_with_user(request.user).get(topic = topic, id = link_id)
    else:
        link = Link.objects.get(topic = topic, id = link_id)
    if request.user.is_authenticated():
        #comments = Comment.objects.get_query_set_with_user(request.user).filter(link = link)#.select_related()
        comments = Comment.objects.append_user_data(Comment.tree.filter(link = link).select_related(), request.user)
    else:
        comments = Comment.tree.filter(link = link).select_related()
    form = bforms.DoComment(user = request.user, link = link)
    tag_form = bforms.AddTag(user = request.user, link = link)
    if request.method == "GET":
        pass    
    if request.method == 'POST':
        import pdb
        #pdb.set_trace()
        if not request.user.is_authenticated():
            return HttpResponseForbidden('Please login')
        if request.POST.has_key('comment'):
            form = bforms.DoComment(user = request.user, link = link, data=request.POST)
            if form.is_valid():
                comment = form.save()
                if request.REQUEST.has_key('ajax'):
                    comment = Comment.objects.get_query_set_with_user(request.user).get(id = comment.id)
                    tem = get_template('news/comment_row.html')
                    context = Context(dict(comment=comment))
                    dom = tem.render(context)
                    payload = dict(text=comment.comment_text, user=comment.user.username, dom=dom)
                    return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
                return HttpResponseRedirect('.')
        elif request.POST.has_key('taglink'):
            tag_form = bforms.AddTag(user = request.user, link = link, data=request.POST)
            if tag_form.is_valid():
                tag, tagged = tag_form.save()
                if request.REQUEST.has_key('ajax'):
                    link_tag = tag.link_tag
                    dom = ('<li><a href="%s">%s</a></li>' % (link_tag.tag.get_absolute_url(), link_tag.tag.text))
                    payload=dict(text=link_tag.tag.text, dom=dom, tagged=tagged)
                    return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
                return HttpResponseRedirect('.')
        elif request.POST.has_key('subcomment'):
            parent_id = int(request.POST['parent_id'])
            parent = Comment.objects.get(id = parent_id)
            subcomment_form = bforms.DoThreadedComment(user = request.user, link=parent.link, parent=parent, data=request.POST)
            if subcomment_form.is_valid():
                comment = subcomment_form.save()
            if request.REQUEST.has_key('ajax'):
                comment = Comment.objects.get_query_set_with_user(request.user).get(id = comment.id)
                tem = get_template('news/comment_row.html')
                context = Context(dict(comment=comment))
                dom = tem.render(context)
                payload = dict(object='comment', action='reply', id=comment.id, text=comment.comment_text, parent_id=comment.parent.id, dom=dom)
                return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
            return HttpResponseRedirect('.')
    payload = {'topic':topic, 'link':link, 'comments':comments, 'form':form, 'tag_form':tag_form}
    return render(request, payload, 'news/link_details.html')

@login_required
def upvote_link(request, link_id):
    if not request.method == 'POST':
        return HttpResponseForbidden('Only Post allowed')
    link = Link.objects.get(id = link_id)
    try:
        link_vote = LinkVote.objects.get(link = link, user = request.user)
        if link_vote.direction:
            vote = link.reset_vote(request.user)
        if not link_vote.direction:
            vote = link.upvote(request.user)
    except LinkVote.DoesNotExist:
        vote = link.upvote(request.user)
    if request.GET.has_key('ajax'):
        payload = {'dir':'up', 'object':'link', 'id':link.id, 'state':vote.direction, 'points':link.vis_points()}
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    return HttpResponseRedirect(link.get_absolute_url())

@login_required
def downvote_link(request, link_id):
    if not request.method == 'POST':
        return HttpResponseForbidden('Only Post allowed')
    link = Link.objects.get(id = link_id)
    try:
        link_vote = LinkVote.objects.get(link = link, user = request.user)
        if not link_vote.direction:
            vote = link.reset_vote(request.user)
        if link_vote.direction:
            vote = link.downvote(request.user)
    except LinkVote.DoesNotExist:
        vote = link.downvote(request.user)
    if request.GET.has_key('ajax'):
        payload = {'dir':'down', 'object':'link', 'id':link.id, 'state':vote.direction, 'points':link.vis_points()}
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    return HttpResponseRedirect(link.get_absolute_url())

@login_required
def save_link(request, link_id):
    if not request.method == 'POST':
        return HttpResponseForbidden('Only Post allowed')
    link = Link.objects.get(id = link_id)
    saved_l = SavedLink.objects.save_link(link = link, user = request.user)
    return HttpResponseRedirect(link.get_absolute_url())
    

def upvote_comment(request, comment_id):
    if not request.method == 'POST':
        return HttpResponseForbidden('Only Post allowed')
    comment = Comment.objects.get(id = comment_id)
    try:
        comment_vote = CommentVote.objects.get(comment = comment, user = request.user)
        if comment_vote.direction:
            vote = comment.reset_vote(request.user)
        if not comment_vote.direction:
            vote = comment.upvote(request.user)
    except CommentVote.DoesNotExist:
        vote = comment.upvote(request.user)
    if request.GET.has_key('ajax'):
        payload = {'dir':'up', 'object':'comment', 'id':comment.id, 'state':vote.direction, 'points':comment.points}
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    return HttpResponseRedirect(comment.link.get_absolute_url())
        
    
    
def downvote_comment(request, comment_id):
    comment = Comment.objects.get(id = comment_id)
    if not request.method == 'POST':
        return HttpResponseForbidden('Only Post allowed')
    try:
        comment_vote = CommentVote.objects.get(comment = comment, user = request.user)
        if not comment_vote.direction:
            vote = comment.reset_vote(request.user)
        if comment_vote.direction:
            vote = comment.downvote(request.user)
    except CommentVote.DoesNotExist:
        vote = comment.downvote(request.user)
    if request.GET.has_key('ajax'):
        payload = {'dir':'down', 'object':'comment', 'id':comment.id, 'state':vote.direction, 'points':comment.points}
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    return HttpResponseRedirect(comment.link.get_absolute_url())

    