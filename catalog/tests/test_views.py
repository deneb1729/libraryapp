from django.test import TestCase
from django.urls import reverse
import datetime
from django.utils import timezone

from catalog.models import Author, BookInstance, Book, Genre, Language
from django.contrib.auth.models import User


class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        number_of_authors = 13
        for author_num in range(number_of_authors):
            Author.objects.create(
                first_name="Christian %s" % author_num, 
                last_name = "Surname %s" % author_num,)
           
    def test_view_url_exists_at_desired_location(self): 
        resp = self.client.get("/catalog/authors/") 
        self.assertEqual(resp.status_code, 200)  
           
    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse("authors"))
        self.assertEqual(resp.status_code, 200)
        
    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse("authors"))
        self.assertEqual(resp.status_code, 200)

        self.assertTemplateUsed(resp, "authors/author_list.html")
        
    def test_pagination_is_ten(self):
        resp = self.client.get(reverse("authors"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("is_paginated" in resp.context)
        self.assertTrue(resp.context["is_paginated"] == True)
        self.assertTrue( len(resp.context["author_list"]) == 10)

    def test_lists_all_authors(self):
        resp = self.client.get(reverse("authors")+"?page=2")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("is_paginated" in resp.context)
        self.assertTrue(resp.context["is_paginated"] == True)
        self.assertTrue( len(resp.context["author_list"]) == 3)


class LoanedBookInstancesByUserListViewTest(TestCase):

    def setUp(self):
        test_user1 = User.objects.create_user(username="testuser1", password="12345") 
        test_user1.save()
        test_user2 = User.objects.create_user(username="testuser2", password="12345") 
        test_user2.save()
        
        test_author = Author.objects.create(first_name="John", last_name="Smith")
        test_genre = Genre.objects.create(name="Fantasy")
        test_language = Language.objects.create(name="English")
        test_book = Book.objects.create(title="Book Title", summary = "My book summary", isbn="ABCDEFG", author=test_author, language=test_language)
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        number_of_book_copies = 30
        for book_copy in range(number_of_book_copies):
            return_date= timezone.now() + datetime.timedelta(days=book_copy%5)
            if book_copy % 2:
                the_borrower=test_user1
            else:
                the_borrower=test_user2
            status="m"
            BookInstance.objects.create(
                book=test_book,
                imprint="Unlikely Imprint, 2016",
                due_back=return_date,
                borrower=the_borrower, 
                status=status)
        
    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse("my-borrowed"))
        self.assertRedirects(resp, "/accounts/login/?next=/catalog/mybooks/")

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("my-borrowed"))
        
        self.assertEqual(str(resp.context["user"]), "testuser1")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "books/bookinstance_list_borrowed_user.html")

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("my-borrowed"))
        
        self.assertEqual(str(resp.context["user"]), "testuser1")
        self.assertEqual(resp.status_code, 200)
        
        self.assertTrue("bookinstance_list" in resp.context)
        self.assertEqual( len(resp.context["bookinstance_list"]),0)
        
        get_ten_books = BookInstance.objects.all()[:10]
        for copy in get_ten_books:
            copy.status="o"
            copy.save()
        
        resp = self.client.get(reverse("my-borrowed"))
        self.assertEqual(str(resp.context["user"]), "testuser1")
        self.assertEqual(resp.status_code, 200)
        
        self.assertTrue("bookinstance_list" in resp.context)
        for bookitem in resp.context["bookinstance_list"]:
            self.assertEqual(resp.context["user"], bookitem.borrower)
            self.assertEqual("o", bookitem.status)

    def test_pages_ordered_by_due_date(self):
    
        for copy in BookInstance.objects.all():
            copy.status="o"
            copy.save()
            
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("my-borrowed"))
        
        self.assertEqual(str(resp.context["user"]), "testuser1")
        self.assertEqual(resp.status_code, 200)
                
        self.assertEqual( len(resp.context["bookinstance_list"]),10)
        
        # Last snippet to analyze
        # *********************************
        last_date=0
        for copy in resp.context["bookinstance_list"]:
            if last_date==0:
                last_date=copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)
        # *********************************