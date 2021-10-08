from .models import *
from .forms import *
from .utils import *

import datetime
import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.defaultfilters import slugify

from _decimal import Decimal

now = timezone.now()


def home(request):
    return render(request, 'crm/home.html',
                  {'crm': home})


@login_required
def customer_list(request):
    customer = Customer.objects.filter(created_date__lte=timezone.now())

    return render(request, 'crm/customer_list.html',
                  {'customers': customer})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        # update
        form = CustomerForm(request.POST, instance=customer)

        if form.is_valid():
            customer = form.save(commit=False)
            customer.updated_date = timezone.now()
            customer.save()
            customer = Customer.objects.filter(created_date__lte=timezone.now())
            return render(request, 'crm/customer_list.html',
                          {'customers': customer})
    else:
        # edit
        form = CustomerForm(instance=customer)

    return render(request, 'crm/customer_edit.html', {'form': form})


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()

    return redirect('crm:customer_list')


@login_required
def service_list(request):
    services = Service.objects.filter(created_date__lte=timezone.now())

    return render(request, 'crm/service_list.html', {'services': services})


@login_required
def service_new(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.created_date = timezone.now()
            service.save()
            services = Service.objects.filter(created_date__lte=timezone.now())

            return render(request, 'crm/service_list.html',
                          {'services': services})

    else:
        form = ServiceForm()

    return render(request, 'crm/service_new.html', {'form': form})


@login_required
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            service = form.save()

            # service.customer = service.id
            service.updated_date = timezone.now()
            service.save()
            services = Service.objects.filter(created_date__lte=timezone.now())

            return render(request, 'crm/service_list.html', {'services': services})

    else:
        form = ServiceForm(instance=service)

    return render(request, 'crm/service_edit.html', {'form': form})


@login_required
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.delete()

    return redirect('crm:service_list')


@login_required
def product_list(request):
    products = Product.objects.filter(created_date__lte=timezone.now())

    return render(request, 'crm/product_list.html', {'products': products})


@login_required
def product_new(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_date = timezone.now()
            product.save()
            products = Product.objects.filter(created_date__lte=timezone.now())

            return render(request, 'crm/product_list.html',
                          {'products': products})

    else:
        form = ProductForm()

    return render(request, 'crm/product_new.html', {'form': form})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()

            # service.customer = service.id
            product.updated_date = timezone.now()
            product.save()
            products = Product.objects.filter(created_date__lte=timezone.now())

            return render(request, 'crm/product_list.html', {'products': products})

    else:
        # print("else")
        form = ProductForm(instance=product)

    return render(request, 'crm/product_edit.html', {'form': form})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()

    return redirect('crm:product_list')


@login_required
def summary(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customers = Customer.objects.filter(created_date__lte=timezone.now())
    services = Service.objects.filter(cust_name=pk)
    products = Product.objects.filter(cust_name=pk)
    sum_service_charge = \
        Service.objects.filter(cust_name=pk).aggregate(Sum('service_charge'))
    sum_product_charge = \
        Product.objects.filter(cust_name=pk).aggregate(Sum('charge'))

    sum = sum_product_charge.get("charge__sum")
    if sum == None:
        sum_product_charge = {'charge__sum': Decimal('0')}
    sum = sum_service_charge.get("service_charge__sum")
    if sum == None:
        sum_service_charge = {'service_charge__sum': Decimal('0')}

    return render(request, 'crm/summary.html', {'customer': customer,
                                                'products': products,
                                                'services': services,
                                                'sum_service_charge': sum_service_charge,
                                                'sum_product_charge': sum_product_charge, })


@login_required
def generate_pdf(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customers = Customer.objects.filter(created_date__lte=timezone.now())
    services = Service.objects.filter(cust_name=pk)
    products = Product.objects.filter(cust_name=pk)
    sum_service_charge = \
        Service.objects.filter(cust_name=pk).aggregate(Sum('service_charge'))
    sum_product_charge = \
        Product.objects.filter(cust_name=pk).aggregate(Sum('charge'))

    template_name = "generate/pdf.html"

    context_dict = {'customer': customer,
                    'products': products,
                    'services': services,
                    'sum_service_charge': sum_service_charge,
                    'sum_product_charge': sum_product_charge,
                    }

    pdf_name = f'{datetime.datetime.now().strftime("%Y-%m-%d")}---{slugify(customer.cust_name)}-summary'

    return render_to_pdf(template_name, pdf_name, context_dict)


@login_required
def generate_csv(request):
    print(request.POST['table'])

    if request.method == 'POST':
        if request.POST['table'] == "service":
            table = Service
        elif request.POST['table'] == "products":
            table = Product
        elif request.POST['table'] == "customers":
            table = Customer

        model_class = table
        meta = model_class._meta

        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        csv_name = f'{datetime.datetime.now().strftime("%Y-%m-%d")}---{slugify(model_class)[15:]}s'
        response['Content-Disposition'] = f'attachment; filename={csv_name}.csv'
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in model_class.objects.all():
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response
