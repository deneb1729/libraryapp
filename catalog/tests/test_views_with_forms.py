from django.contrib.auth.models import Permission 
from django.test import TestCase
from django.urls import reverse
import datetime

from catalog.models import Author, BookInstance, Book, Genre, Language
from django.contrib.auth.models import User

class RenewBookInstancesViewTest(TestCase):

    def setUp(self):
        test_user1 = User.objects.create_user(
            username="testuser1", 
            password="12345")
        test_user1.save()

        test_user2 = User.objects.create_user(
            username="testuser2", 
            password="12345")
        test_user2.save()
        permission = Permission.objects.get(
                        name="Set book as returned")
        test_user2.user_permissions.add(permission)
        test_user2.save()

        test_author = Author.objects.create(
                        first_name="John", 
                        last_name="Smith")
        test_genre = Genre.objects.create(name="Fantasy")
        test_language = Language.objects.create(name="English")
        test_book = Book.objects.create(
                        title="Book Title", 
                        summary = "My book summary", 
                        isbn="ABCDEFG", 
                        author=test_author, 
                        language=test_language,)
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        return_date= datetime.date.today() + datetime.timedelta(days=5)

        self.test_bookinstance1=BookInstance.objects.create(
                                    book=test_book,
                                    imprint="Unlikely Imprint, 2016", 
                                    due_back=return_date, 
                                    borrower=test_user1, 
                                    status="o")

        self.test_bookinstance2=BookInstance.objects.create(
                                    book=test_book,
                                    imprint="Unlikely Imprint, 2016", 
                                    due_back=return_date, 
                                    borrower=test_user2, 
                                    status="o")
                        
    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(
                    reverse(
                        "renew-book-librarian", 
                        kwargs={"pk":self.test_bookinstance1.pk,}) )
        self.assertEqual( resp.status_code,302)
        self.assertTrue( resp.url.startswith("/accounts/login/") )
        
    def test_redirect_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(
                    username="testuser1", 
                    password="12345")
        resp = self.client.get(
                    reverse(
                        "renew-book-librarian", 
                        kwargs={"pk":self.test_bookinstance1.pk,}) )
        
        self.assertEqual( resp.status_code,302)
        self.assertTrue( resp.url.startswith("/accounts/login/") )

    def test_logged_in_with_permission_borrowed_book(self):
        login = self.client.login(
                    username="testuser2", 
                    password="12345")
        resp = self.client.get(
                    reverse(
                        "renew-book-librarian", 
                        kwargs={"pk":self.test_bookinstance2.pk,}) )
        
        self.assertEqual( resp.status_code,200)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        login = self.client.login(
                    username="testuser2", 
                    password="12345")
        resp = self.client.get(
                    reverse(
                        "renew-book-librarian", 
                        kwargs={"pk":self.test_bookinstance1.pk,}) )
        
        self.assertEqual( resp.status_code,200)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        import uuid 
        test_uid = uuid.uuid4()
        login = self.client.login(
                    username="testuser2", 
                    password="12345")
        resp = self.client.get(
                reverse(
                    "renew-book-librarian", 
                    kwargs={"pk":test_uid,}) )
        self.assertEqual( resp.status_code,404)
        
    def test_uses_correct_template(self):
        login = self.client.login(
                    username="testuser2", 
                    password="12345")
        resp = self.client.get(
                reverse(
                    "renew-book-librarian", 
                    kwargs={"pk":self.test_bookinstance1.pk,}) )
        self.assertEqual( resp.status_code,200)

        self.assertTemplateUsed(resp, "books/book_renew_librarian.html")

    def test_form_renewal_date_initially_has_date_two_weeks_in_future(self):
        login = self.client.login(
                    username="testuser2", 
                    password="12345")
        resp = self.client.get(
                reverse(
                    "renew-book-librarian", 
                    kwargs={"pk":self.test_bookinstance1.pk,}) )
        
        date_2_weeks_in_future = (
            datetime.date.today() + 
            datetime.timedelta(weeks=2)) 
            
        self.assertEqual(
            resp.context["form"].initial["due_back"], 
            date_2_weeks_in_future )

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        login = self.client.login(
                    username="testuser2", 
                    password="12345")
        valid_date_in_future = (
            datetime.date.today() + 
            datetime.timedelta(weeks=2))
        resp = self.client.post(
                reverse(
                    "renew-book-librarian", 
                    kwargs={"pk":self.test_bookinstance1.pk,}), 
                {"due_back":valid_date_in_future} )
        self.assertRedirects(
            resp, 
            reverse("all-borrowed") )

    def test_form_invalid_renewal_date_past(self):
        login = self.client.login(username="testuser2", password="12345")       
        date_in_past = datetime.date.today() - \
            datetime.timedelta(weeks=1)
        resp = self.client.post(
                reverse(
                    "renew-book-librarian", 
                    kwargs={"pk":self.test_bookinstance1.pk,}), 
                {"due_back":date_in_past} )
        self.assertEqual( resp.status_code,200)
        self.assertFormError(
            resp, 
            "form", 
            "due_back", 
            "Invalid date - renewal in past")
        
    def test_form_invalid_renewal_date_future(self):
        login = self.client.login(
                    username="testuser2", 
                    password="12345")
        invalid_date_in_future = datetime.date.today() + \
            datetime.timedelta(weeks=5)
        resp = self.client.post(
                reverse(
                    "renew-book-librarian", 
                    kwargs={"pk":self.test_bookinstance1.pk,}), 
                {"due_back":invalid_date_in_future} )
        self.assertEqual( resp.status_code,200)
        self.assertFormError(
            resp, 
            "form", 
            "due_back", 
            "Invalid date - renewal more than 3 weeks ahead")