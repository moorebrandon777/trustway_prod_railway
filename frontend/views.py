from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.template.loader import render_to_string
from django.contrib.auth import login as auth_login
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login

from django.core.mail import send_mail
from django.http import HttpResponseRedirect

from django.urls import reverse_lazy
from account.models import CustomUser
from account.forms import UserLoginForm, UserRegisterForm, UserBankAccountForm
from transactions import emailsend

class HomeView(TemplateView):
    template_name = 'frontend3/index.html'
    # template_name = 'frontend2/index.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return HttpResponseRedirect(reverse_lazy('account:admin_dashboard'))
            else:
                return HttpResponseRedirect(reverse_lazy('account:customer_dashboard'))
        return super().dispatch(request, *args, **kwargs)


class AboutUsView(TemplateView):
    template_name = 'frontend/about.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return HttpResponseRedirect(reverse_lazy('account:admin_dashboard'))
            else:
                return HttpResponseRedirect(reverse_lazy('account:customer_dashboard'))
        return super().dispatch(request, *args, **kwargs)


class ContactUsView(TemplateView):
    template_name = 'frontend/contact.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return HttpResponseRedirect(reverse_lazy('account:admin_dashboard'))
            else:
                return HttpResponseRedirect(reverse_lazy('account:customer_dashboard'))
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        name = self.request.POST.get('name')
        email = self.request.POST.get('email')
        subject = self.request.POST.get('subject')
        message = self.request.POST.get('message')
        final_message = render_to_string('emails/customer_care_email.html', 
        {
            'name': name,
            'email': email,
            'message': message,
            'subject': subject
        })
        try:
            emailsend.email_send(
                'Email From '+name,
                final_message,
                'customerservice@hmb-online.com',
            )
            messages.success(self.request, 'Email sent successfully, we will get back to you as soon as possible')
        except:
            messages.error(self.request, 'There was an error while trying to send your email, please try again')

        finally:
            return HttpResponseRedirect(reverse_lazy('frontend:contact_us'))


class RegisterUserView(CreateView):
    redirect_authenticated_user = True
    template_name = 'frontend3/register.html'
    # template_name = 'frontend2/register.html'
    model = CustomUser
    form_class = UserRegisterForm

    def get_success_url(self):
        return reverse_lazy('frontend:register')
    
    def form_valid(self, form):
        ctx = self.get_context_data()
        form2 = ctx['form2']
        if form.is_valid() and form2.is_valid():
            self.object = form.save()
            bank_account = form2.save(commit=False)
            bank_account.user = self.object
            bank_account.account_no = self.object.account_number
            bank_account.save()
            messages.success(self.request, 'Account Created Successfully')
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))
        
    def get_context_data(self, **kwargs):
        ctx = super(RegisterUserView, self).get_context_data(**kwargs)
        if self.request.POST:
            ctx['form'] = UserRegisterForm(self.request.POST)
            ctx['form2'] = UserBankAccountForm(self.request.POST)
        else:
            ctx['form'] = UserRegisterForm()
            ctx['form2'] = UserBankAccountForm()
        return ctx


class LoginUserView(LoginView):
    redirect_authenticated_user = True
    form_class = UserLoginForm
    template_name = 'frontend3/login.html'
    # template_name = 'frontend2/index.html'

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse_lazy('account:admin_dashboard')
        else:
            return reverse_lazy('account:customer_dashboard')
        
    def form_valid(self, form):
        user = form.get_user()
        customer = CustomUser.objects.get(email=user.email)
        if customer.is_activated:
            auth_login(self.request, form.get_user())
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.error(self.request,'This account is not activated, please contact our customer service for activation of your account')
            return self.render_to_response(self.get_context_data(form=form))
    def form_invalid(self, form):
        messages.error(self.request,'Invalid login cridentials, please check the details and try again')
        return self.render_to_response(self.get_context_data(form=form))
    

def login_index_form(request):
    if request.method == 'POST':
        username = request.POST['email']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            customer = CustomUser.objects.get(email=user.email)
            if customer.is_activated:
                login(request, user)
                if user.is_staff:
                    return redirect('account:admin_dashboard')
                else:
                    return redirect('account:customer_dashboard')
            else:
                messages.error(request,'This account is deactivated, please contact our customer service for activation of your account')
                return redirect("frontend:home")
        else:
            messages.error(request,'Invalid login cridentials, please check the details and try again')
            return redirect("frontend:home")