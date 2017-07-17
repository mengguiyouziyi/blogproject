from django.shortcuts import render, get_object_or_404, redirect
from .models import Comment
from .forms import CommentForm
from blog.models import Post


def post_comment(request, post_pk):
	post = get_object_or_404(Post, pk=post_pk)
	if request.method == 'POST':
		form = CommentForm(request.POST)
		if form.is_valid():
			comment = form.save(commit=False)
			comment.post = post
			comment.save()
			return redirect(post)

		else:
			comment_list = post.comment_set.all()
			context = {
				'post': post,
				'form': form,
				'comment_list': comment_list
			}
			# 其他内容一样，只是要渲染错误提示和表单
			return render(request, 'blog/index.html', context=context)
	return redirect(post)