import datetime
from django.shortcuts import render
from django.views.generic import ListView
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .models import Book, Author, BookInstance, Genre
from .forms import RenewBookModelForm

def index(request):
    num_books=Book.objects.all().count()
    num_instances=BookInstance.objects.all().count()
    num_instances_available=BookInstance.objects.filter(status__exact="a").count()
    num_authors=Author.objects.count()  
    num_genres=Genre.objects.count()
    books_madagascar=Book.objects.filter(title__iexact="madagascar")
    
    num_visits = request.session.get("num_visits", 0)
    request.session["num_visits"] = num_visits + 1
    
    context = {
        "num_books":num_books,
        "num_instances":num_instances,
        "num_instances_available":num_instances_available,
        "num_authors":num_authors,
        "num_genres": num_genres,
        "num_visits":num_visits,
    } 

    return render(
        request,
        "index.html",
        context=context,
    )


class AuthorListView(ListView):
    model = Author
    paginate_by = 10
    template_name = "authors/author_list.html"


def AuthorDetailView(request,pk):
    author_id=get_object_or_404(Author, pk=pk)
    
    return render(
        request,
        "authors/author_detail.html",
        context={"author":author_id,}
    )


class BookListView(ListView):
    model = Book
    paginate_by = 3
    context_object_name = "book_list"
    template_name = "books/book_list.html"

    def get_context_data(self, **kwargs):
        context = super(BookListView, self).get_context_data(**kwargs)
        context["some_data"] = "This is just some data"
        return context




def BookDetailView(request,pk):
    book_id=get_object_or_404(Book, pk=pk)
    
    return render(
        request,
        "books/book_detail.html",
        context={"book":book_id,}
    )

class LoanedBooksByUserListView(LoginRequiredMixin,ListView):
    model = BookInstance
    template_name ="books/bookinstance_list_borrowed_user.html"
    paginate_by = 10
    
    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact="o").order_by("due_back")


class BorrowedBooksListView(PermissionRequiredMixin,ListView):
    model = BookInstance
    template_name ="books/bookinstance_list_borrowed_user.html"
    paginate_by = 10
    permission_required = "catalog.can_mark_returned"

    def get_queryset(self):
        return BookInstance.objects.order_by("id")


@permission_required("catalog.can_mark_returned")
def renew_book_librarian(request, pk):
    book_inst=get_object_or_404(BookInstance, pk = pk)

    if request.method == "POST":
        form = RenewBookModelForm(request.POST)

        if form.is_valid():
            book_inst.due_back = form.cleaned_data["due_back"]
            book_inst.save()
            return HttpResponseRedirect(reverse("all-borrowed") )

    else:
        proposed_due_back = datetime.date.today() + datetime.timedelta(weeks=2)
        form = RenewBookModelForm(initial={"due_back": proposed_due_back,})

    return render(request, "books/book_renew_librarian.html", {"form": form, "bookinst":book_inst})


class AuthorCreate(PermissionRequiredMixin,CreateView):
    model = Author
    template_name ="authors/author_form.html"
    permission_required = "catalog.add_author"
    fields = "__all__"
    initial={"date_of_birth":"05/01/2018",}


class AuthorUpdate(PermissionRequiredMixin,UpdateView):
    model = Author
    template_name ="authors/author_form.html"
    permission_required = "catalog.change_author"
    fields = ["first_name","last_name","date_of_birth","date_of_death"]


class AuthorDelete(PermissionRequiredMixin,DeleteView):
    model = Author
    template_name ="authors/author_confirm_delete.html"
    permission_required = "catalog.delete_author"
    success_url = reverse_lazy("authors")


class BookCreate(PermissionRequiredMixin,CreateView):
    model = Book
    template_name ="books/book_form.html"
    permission_required = "catalog.add_book"
    fields = "__all__"
    initial={"status":"a",}


class BookUpdate(PermissionRequiredMixin,UpdateView):
    model = Book
    template_name ="books/book_form.html"
    permission_required = "catalog.change_book"
    fields = "__all__"


class BookDelete(PermissionRequiredMixin,DeleteView):
    model = Book
    template_name ="books/book_confirm_delete.html"
    permission_required = "catalog.delete_book"
    success_url = reverse_lazy("books")