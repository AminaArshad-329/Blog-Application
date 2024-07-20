from django.shortcuts import render,get_object_or_404
from django.contrib.postgres.search import SearchVector
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .models import Comment, Post
from django.views.generic.list import ListView
from django.core.mail import send_mail
from .forms import EmailPostForm,CommentForm
from django.db.models import Count
from taggit.models import Tag


# Create your views here.
# class PostListView(ListView):
#     queryset = Post.objects.all()
#     model = Post
#     paginate_by = 2
#     context_object_name = 'posts'
#     template_name = 'blog/post/list.html'


def post_share(request, post_id):
    #retrive post by #
    post = get_object_or_404(Post, id=post_id, status='published')
    sent=False
    if request.method == 'POST':
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form passes validation
            cd = form.cleaned_data
            #...send Email
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recomends you read {post.title}"
            message = f" Read {post.title} at {post_url}\n\n" \
                      f" {cd['name']}\s comments: {cd['comments']}"
            send_mail('Django mail', 'This e-mail was sent with Django.', 'sarach8485@gmail.com', ['amina.arshad.argonteq@gmail.com'], fail_silently=False)
            sent=True
    else:
        form = EmailPostForm()
    context = {
        'form':form,
        'post':post,
        'sent': sent
        }
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})

# List of active comments for this post
def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status='published', publish__year=year, publish__month=month, publish__day=day)
    comments = Comment.objects.filter(active=True, post=post)
    new_comment = None
    if request.method == 'POST':
        # A comment was posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Create Comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.post = post
            # Save the comment to the database
            new_comment.save()
    else:
        comment_form = CommentForm()
    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.objects.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
    return render(request, 'blog/post/detail.html', {'post': post, 'comments': comments, 'new_comment': new_comment, 'comment_form': comment_form,'similar_posts': similar_posts})


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', 'body')
            search_query = SearchQuery(query)
            results = Post.objects.annotate( search=search_vector, rank=SearchRank(search_vector, search_query) ).filter(search=search_query).order_by('-rank')
            #     similarity=TrigramSimilarity('title', query),
            # ).filter(similarity__gt=0.1).order_by('-similarity')
    return render(request,
                  'blog/post/search.html',
                  {'form': form,
                   'query': query,
                   'results': results})


# valid
# def post_share(request, post_id):
#     post = get_object_or_404(Post, id=post_id, status='published')
#     sent = False
#     if request.method == 'POST':
#         # Form was submitted
#         form = EmailPostForm(request.POST)
#         if form.is_valid():
#             # Form fields passed validation
#             cd = form.cleaned_data
#             post_url = request.build_absolute_uri(post.get_absolute_url())
#             subject = f"{cd['name']} recommends you read " \
#                       f"{post.title}"

#             message = f"Read {post.title} at {post_url}\n\n" \
#                       f"{cd['name']}\'s comments: {cd['comments']}"
#             # send_mail(subject, message, 'amina.arshad.argonteq@gmail.com',[cd['sarach8485@gmail.com']])
#             send_mail('Django mail', 'This e-mail was sent with Django.', 'sarach8485@gmail.com', ['amina.arshad.argonteq@gmail.com'], fail_silently=False)
#             sent = True
#     else:
#         form = EmailPostForm()
#     return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})
# ...........................................................................................................

# def post_share(request, post_id):
#     # Retrieve post by id
#     post = get_object_or_404(Post, id=post_id, status='published')
#     sent = False 
 
#     if request.method == 'POST':
#         # Form was submitted
#         form = EmailPostForm(request.POST)
#         if form.is_valid():
#             # Form fields passed validation
#             cd = form.cleaned_data
#             post_url = request.build_absolute_uri(post.get_absolute_url())
#             subject = '{} ({}) recommends you reading "{}"'.format(cd['name'], cd['amina.arshad.argonteq@gmail.com'], post.title)
#             message = 'Read "{}" at {}\n\n{}\'s comments: {}'.format(post.title, post_url, cd['name'], cd['comments'])
#             send_mail(subject, message, 'sarach8485@gmail.com',[cd['amina.arshad.argonteq@gmail.com']])
#             sent = True
#     else:
#         form = EmailPostForm()
#     return render(request, 'blog/post/share.html', {'post': post,'form': form,'sent': sent})
# ...........................................................
def post_list(request, tag_slug=None):
    object_list = Post.objects.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])
    paginator = Paginator(object_list, 2) # 2 posts in each page
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
    # If page is not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
    # If page is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'page': page, 'posts': posts , 'tag': tag})

# def post_detail(request, year, month, day, post):
#     post = get_object_or_404(Post, slug=post, status='published', publish__year=year, publish__month=month, publish__day=day)
#     return render(request, 'blog/post/detail.html', {'post': post})
    

# def post_share(request, post_id):
#  # Retrieve post by id
#     post = get_object_or_404(Post, id=post_id, status='published')
#     if request.method == 'POST':
#     # Form was submitted
#         form = EmailPostForm(request.POST)
#     if form.is_valid():
#     # Form fields passed validation
#         cd = form.cleaned_data
#     # ... send email
#     else:
#         form = EmailPostForm()
#     return render(request, 'blog/post/share.html', {'post': post,'form': form})



