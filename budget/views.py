from django.shortcuts import render,redirect
from django.views.generic import View
from budget.models import Transaction
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.utils import timezone
from django.db.models import Sum
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.decorators.cache import never_cache


def signin_required(fn):
    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated:
            messages.error(request,"invalid session")
            return redirect("signin")
        else:
            return fn(request,*args,**kwargs)
    return wrapper


decs=[signin_required,never_cache]

class TransactionForm(forms.ModelForm):         # modelform class have meta class inside 
    class Meta:                                 # meta class contain model and either fields or exclude
        model=Transaction
        # fields="__all__"                      # use when all fields from model required in form
        # fields=["field1","field2",....]       # use when specify required fields in a list
        exclude=("created_date","user_object")              # use to exclude fields from form (tuple)
        widgets={
            "title":forms.TextInput(attrs={"class":"form-control"}),
            "amount":forms.NumberInput(attrs={"class":"form-control"}),
            "type":forms.Select(attrs={"class":"form-control form-select"}),
            "category":forms.Select(attrs={"class":"form-control form-select"}),
        }




class RegistrationForm(forms.ModelForm):
    class Meta:
        model=User
        fields=["username","email","password"]
        widgets={
            "username":forms.TextInput(attrs={"class":"form-control"}),
            "email":forms.EmailInput(attrs={"class":"form-control"}),
            "password":forms.PasswordInput(attrs={"class":"form-control"})
        }



class LoginForm(forms.Form):       # model form not used bcz it uses when we have creation and updation 
    username=forms.CharField(widget=forms.TextInput(attrs={"class":"form-control"}))
    password=forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control"}))



# view for listing all transactions
# lh:8000/transactions/all
# method: get


@method_decorator(decs,name="dispatch")
class TransactionListView(View):
    def get(self,request,*args,**kwargs):
        qs=Transaction.objects.filter(user_object=request.user)

        cur_month=timezone.now().month
        cur_year=timezone.now().year
        # print(cur_month,cur_year)
        # exp_total=Transaction.objects.filter(
        #     user_object=request.user,
        #     type="expense",
        #     created_date__month=cur_month,
        #     created_date__year=cur_year
        # ).aggregate(Sum("amount"))
        # print(exp_total)

        # income_total=Transaction.objects.filter(
        #     user_object=request.user,
        #     type="income",
        #     created_date__month=cur_month,
        #     created_date__year=cur_year
        # ).aggregate(Sum("amount"))
        # print(income_total)


        data=Transaction.objects.filter(
            user_object=request.user,
            created_date__month=cur_month,
            created_date__year=cur_year
        ).values("type").annotate(type_sum=Sum("amount"))
        print(data)

        cat_qs=Transaction.objects.filter(
            user_object=request.user,
            created_date__month=cur_month,
            created_date__year=cur_year
        ).values("category").annotate(category_sum=Sum("amount"))
        print(cat_qs)
        
        return render(request,"transaction_list.html",{"data":qs,"type_total":data,"category_total":cat_qs})
    




# view for creating transactions
# lh:/8000/transactions/add
# method:get,post

@method_decorator(decs,name="dispatch")    
class TransactionCreateView(View):
    def get(self,request,*args,**kwargs):
        form=TransactionForm()
        return render(request,"transaction_add.html",{"form":form})
    
    def post(self,request,*args,**kwargs):
        form=TransactionForm(request.POST)
        if form.is_valid():
            data=form.cleaned_data
            Transaction.objects.create(**data,user_object=request.user)
            # form.save()
            messages.success(request,"transaction has been added successfully")
            return redirect("transaction-list")
        else:
            messages.error(request,"failed to add transaction")
            return render(request,"transaction_add.html",{"form":form})
        





# Transaction Detail View
# url: lh:8000/transactions/{id}/
# method: get

@method_decorator(decs,name="dispatch")        
class TransactionDetailView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        qs=Transaction.objects.get(id=id)                       
        return render(request,"transaction_detail.html",{"data":qs})
    



# Transaction Delete View
# url: lh:8000/transactions/{id}/remove
# method: get
    
@method_decorator(decs,name="dispatch")   
class TransactionDeleteView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        Transaction.objects.filter(id=id).delete()
        messages.success(request,"transaction has been removed")
        return redirect("transaction-list")
    


# Transaction Update View
# url: lh:8000/transactions/{id}/change
# method: get, post
    
@method_decorator(decs,name="dispatch")   
class TransactionUpdateView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        transaction_object=Transaction.objects.get(id=id)
        form=TransactionForm(instance=transaction_object)
        return render(request,"transaction_edit.html",{"form":form})
    
    def post(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        transaction_object=Transaction.objects.get(id=id)
        form=TransactionForm(request.POST,instance=transaction_object)
        if form.is_valid():
            form.save()
            messages.success(request,"transaction has been updated successfully")
            return redirect("transaction-list") 
        else:
            messages.error(request,"edit transaction failed")
            return render(request,"transaction_edit.html",{"form":form})
        



# Signup
# url: lh:8000/signup/
# method: get,post
        

class SignUpView(View):
    def get(self,request,*args,**kwargs):
        form=RegistrationForm()
        return render(request,"register.html",{"form":form})
    
    def post(self,request,*args,**kwargs):
        form=RegistrationForm(request.POST)
        if form.is_valid():
            # form.save()
            User.objects.create_user(**form.cleaned_data)  # encrypt password
            print("record has been added")
            return redirect("signin")
        else:
            print("failed to create record")
            return render(request,"register.html",{"form":form})




#Signin
# url: lh:8000/signin/
# method: get,post
        
class SignInView(View):
    def get(self,request,*args,**kwargs):
        form=LoginForm()
        return render(request,"signin.html",{"form":form})
    
    def post(self,request,*args,**kwargs):
        form=LoginForm(request.POST)
        if form.is_valid():
            u_name=form.cleaned_data.get("username")
            pwd=form.cleaned_data.get("password")
            user_object=authenticate(request,username=u_name,password=pwd)
            if user_object:
                login(request,user_object)
                print("valid")
                return redirect("transaction-list")
        print("invalid")
        return render(request,"signin.html",{"form":form})



@method_decorator(decs,name="dispatch")   
class SignOutView(View):
    def get(self,request,*args,**kwargs):
        logout(request)
        return redirect("signin")




# never cashe