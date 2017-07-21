# from django.http import HttpResponse
import markdown
from django.shortcuts import render, get_object_or_404
from .models import Post, Category, Tag
from comments.forms import CommentForm
from django.views.generic import ListView, DetailView
from django.utils.text import slugify
from markdown.extensions.toc import TocExtension
from django.db.models import Q


def search(request):
	q = request.GET.get('q')
	error_msg = ''
	if not q:
		error_msg = '请输入关键词'
		return render(request, 'blog/index.html', {'error_msg': error_msg})

	post_list = Post.objects.filter(Q(title__icontains=q) | Q(body__icontains=q))
	return render(request, 'blog/index.html', {'error_msg': error_msg, 'post_list': post_list})


class IndexView(ListView):
	model = Post
	template_name = 'blog/index.html'
	context_object_name = 'post_list'
	paginate_by = 3

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		paginator = context.get('paginator')
		page = context.get('page_obj')
		is_paginated = context.get('is_paginated')
		pagination_data = self.pagination_data(paginator, page, is_paginated)
		context.update(pagination_data)

		return context


	def pagination_data(self, paginator, page, is_paginated):
		if not is_paginated:
			return {}
		# 当前页左边连续的页码号，初始值为空
		left = []
		right = []

		# 标示第 1 页页码后是否需要显示省略号
		left_has_more = False
		right_has_more = False

		# 是否需要显示第一页
		first = False
		last = False

		# 用户请求的当前页码
		page_number = page.number

		total_pages = paginator.num_pages

		# 获得整个分页页码列表，比如分了四页，那么就是 [1, 2, 3, 4]
		page_range = paginator.page_range

		if page_number == 1:
			right = page_range[page_number:page_number+2]

			if right[-1] < total_pages - 1:
				right_has_more = True

			if right[-1] < total_pages:
				last = True
		elif page_number == total_pages:
			# 假如共4页，page_range[1]是第二个元素，page_range[3]代表第四个元素，但是不取
			# 假如3页，page_range[0]
			# 假如2页，page_range[-1]
			left = page_range[(page_number-3) if (page_number-3) > 0 else 0:page_number-1]

			if left[0] > 2:
				left_has_more = True

			if left[0] > 1:
				first = True
		else:
			left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]
			right = page_range[page_number:page_number + 2]
			if right[-1] < total_pages - 1:
				right_has_more = True
			if right[-1] < total_pages:
				last = True
			if left[0] > 2:
				left_has_more = True
			if left[0] > 1:
				first = True

		data = {
			'left': left,
			'right': right,
			'left_has_more': left_has_more,
			'right_has_more': right_has_more,
			'first': first,
			'last': last,
		}
		return data


class CategoryView(IndexView):
	def get_queryset(self):
		cate = get_object_or_404(Category, pk=self.kwargs.get('pk'))
		return super(CategoryView, self).get_queryset().filter(category=cate)


class TagView(IndexView):
	def get_queryset(self):
		tag = get_object_or_404(Tag, pk=self.kwargs.get('pk'))
		return super(TagView, self).get_queryset().filter(tags=tag)


class ArchivesView(IndexView):
	def get_queryset(self):
		year = self.kwargs.get('year')
		month = self.kwargs.get('month')
		return super(ArchivesView, self).get_queryset().filter(created_time__year=year, created_time__month=month)


class PostDetailView(DetailView):
	model = Post
	template_name = 'blog/detail.html'  #detail.html
	context_object_name = 'post'

	def get(self, request, *args, **kwargs):
		response = super(PostDetailView, self).get(request, *args, **kwargs)
		self.object.increase_views()
		return response

	# def get_object(self, queryset=None):
	# 	post = super(PostDetailView, self).get_object(queryset=None)
	# 	post.body = markdown.markdown(post.body, extensions=[
	# 		'markdown.extensions.extra',
	# 		'markdown.extensions.codehilite',
	# 		'markdown.extensions.toc'
	# 	])
	# 	return post

	def get_object(self, queryset=None):
		post = super(PostDetailView, self).get_object(queryset=None)
		md = markdown.Markdown(extensions=[
			'markdown.extensions.extra',
			'markdown.extensions.codehilite',
			TocExtension(slugify=slugify),
		])
		post.body = md.convert(post.body)
		post.toc = md.toc

		return post

	def get_context_data(self, **kwargs):
		context = super(PostDetailView, self).get_context_data(**kwargs)
		form = CommentForm()
		comment_list = self.object.comment_set.all()
		context.update({
			'form': form,
			'comment_list': comment_list
		})
		return context


# class PostDetailView(DetailView):
#     model = Post
#     template_name = 'blog/detail.html'
#     context_object_name = 'post'
#
#     def get(self, request, *args, **kwargs):
#         # 覆写 get 方法的目的是因为每当文章被访问一次，就得将文章阅读量 +1
#         # get 方法返回的是一个 HttpResponse 实例
#         # 之所以需要先调用父类的 get 方法，是因为只有当 get 方法被调用后，
#         # 才有 self.object 属性，其值为 Post 模型实例，即被访问的文章 post
#         response = super(PostDetailView, self).get(request, *args, **kwargs)
#
#         # 将文章阅读量 +1
#         # 注意 self.object 的值就是被访问的文章 post
#         self.object.increase_views()
#
#         # 视图必须返回一个 HttpResponse 对象
#         return response
#
#     def get_object(self, queryset=None):
#         # 覆写 get_object 方法的目的是因为需要对 post 的 body 值进行渲染
#         post = super(PostDetailView, self).get_object(queryset=None)
#         post.body = markdown.markdown(post.body,
#                                       extensions=[
#                                           'markdown.extensions.extra',
#                                           'markdown.extensions.codehilite',
#                                           'markdown.extensions.toc',
#                                       ])
#         return post
#
#     def get_context_data(self, **kwargs):
#         # 覆写 get_context_data 的目的是因为除了将 post 传递给模板外（DetailView 已经帮我们完成），
#         # 还要把评论表单、post 下的评论列表传递给模板。
#         context = super(PostDetailView, self).get_context_data(**kwargs)
#         form = CommentForm()
#         comment_list = self.object.comment_set.all()
#         context.update({
#             'form': form,
#             'comment_list': comment_list
#         })
#         # return context


# def detail(request, pk):
# 	post = get_object_or_404(Post, pk=pk)
#
# 	post.increase_views()
#
# 	post.body = markdown.markdown(post.body, extensions=[
# 		'markdown.extensions.extra',
# 		'markdown.extensions.codehilite',
# 		'markdown.extensions.toc',
# 	])
# 	form = CommentForm()
# 	comment_list = post.comment_set.all()
# 	context = {
# 		'post': post,
# 		'form': form,
# 		'comment_list': comment_list
# 	}
# 	# 绑定的是detail页面url
# 	return render(request, 'blog/detail.html', context=context)


# def archives(request, year, month):
# 	post_list = Post.objects.filter(created_time__year=year, created_time__month=month)
# 	return render(request, 'blog/index.html', context={'post_list': post_list})

