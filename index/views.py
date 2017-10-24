from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.timezone import localtime
from passlib.apps import custom_app_context as pwd_context

from .models import User, Purchase, SalePrice, Buyer, Transaction
from .utils import render_to_pdf, write_to_excel


# Handles home
def home(request):
    # checks whether user is logged in or not
    if not authenticated(request):
        return redirect('login')

    # gets user from database
    user = User.objects.get(id=request.session["user_id"])

    # gets all the items purchased by the user

    return render(request, "index/home.html", {"authenticated": True, })


# Handles registration
def register(request):
    if request.method == "POST":

        # if name is blank
        if not request.POST.get("name"):
            return render(request, "index/register.html", {"n_message": "Name field cannot be empty."})

        # if username blank or less than 5 character, return error
        if not request.POST.get("username") or len(request.POST.get("username")) < 5:
            return render(request, "index/register.html", {"n_message": "Invalid username."})

        # if password blank or less than 6 character or didn't match, return error
        elif not request.POST.get("password") or request.POST.get("password") != request.POST.get("verifypassword") \
                or len(request.POST.get("password")) > 6:
            return render(request, "index/register.html", {"n_message": "Invalid password."})

        # converts password into hash
        pwd_hash = pwd_context.hash(request.POST.get("password"))

        # creates a new User object
        user = User(username=(request.POST.get("username")).lower(), hash=pwd_hash, name=request.POST.get("name"))

        # saves User object into the database
        try:
            user.save()
        except IntegrityError as e:
            # if user already exists, return error
            if 'unique constraint' in e.args[0]:
                return render(request, "index/register.html", {"n_message": "Username already taken."})
            return render(request, "index/register.html", {"n_message": e})

        # create session and redirect to home
        request.session["user_id"] = user.id
        return redirect('home')

    # check if user is logged in
    elif authenticated(request):
        return redirect('home')

    # if request is "GET"
    return render(request, "index/register.html", {})


# handles login
def login(request):
    if request.method == "POST":

        # if username blank or less than 5 character, return error
        if not request.POST.get("username") or len(request.POST.get("username")) < 5:
            return render(request, "index/login.html", {"n_message": "Invalid username."})

        # if password blank or less than 6 character, return error
        elif not request.POST.get("password") or len(request.POST.get("password")) > 6:
            return render(request, "index/login.html", {"n_message": "Invalid password."})

        # gets user from database
        user = User.objects.filter(username=(request.POST.get("username")).lower())

        # if user is found in database
        if user.exists() and len(user) == 1:
            for info in user:
                # if password matches, create session and redirect to home
                if pwd_context.verify(request.POST.get("password"), info.hash):
                    request.session["user_id"] = info.id
                    return redirect('home')

        # username or password didn't match, show error
        return render(request, "index/login.html", {"n_message": "Invalid username/password."})

    # check if user is logged in
    elif authenticated(request):
        return redirect('home')

    # if request is "GET"
    return render(request, "index/login.html", {})


# handles logout
def logout(request):
    # try to delete user session, if error, return to login
    try:
        del request.session["user_id"]
        request.session.flush()
    except KeyError:
        return redirect('login')

    return redirect('login')


# handles stock
def stock(request):

    # checks whether user is authenticated or not
    if not authenticated(request):
        return redirect('login')

    # sets authentication to true for templates
    context = {"authenticated": True}

    # sets initial errors to false
    invalid_pid = 0
    invalid_sprice = 0
    success_save = 0

    # if an error exists, updates its variable and deletes its cookie
    try:
        invalid_pid = request.session["i_p"]
        del request.session["i_p"]
    except KeyError:
        pass

    # if an error exists, updates its variable and deletes its cookie
    try:
        invalid_sprice = request.session["i_sp"]
        del request.session["i_sp"]
    except KeyError:
        pass

    # if a success exists, updates its variable and deletes its cookie
    try:
        success_save = request.session["s_s"]
        del request.session["s_s"]
    except KeyError:
        pass

    # if any error/success exists, display respective message
    if invalid_pid:
        context["n_message"] = "Invalid PID"
    elif invalid_sprice:
        context["n_message"] = "Invalid Sale Price"
    elif success_save:
        context["p_message"] = "Sale Price updated successfully."

    # blank list to hold all the items in stock
    items = []

    # queryset of all objects in purchase model
    qs = Purchase.objects.all()

    # loops over qs
    for instance in qs:
        # gets respective item from SalePrice model
        sale_item = SalePrice.objects.get(pid=instance)

        # converts object to dictionary, so new keys can be added
        item = model_to_dict(instance)

        # if sale price is not set, set keys to NaN so that when editing in stock page, respective fields show nothing
        if sale_item.sale_price is None:
            item["sale_price"] = ""
            item["sale_tax"] = ""
            item["sale_total"] = ""

        # else set keys to respective values
        else:
            item["sale_price"] = sale_item.sale_price
            item["sale_tax"] = sale_item.sale_tax
            item["sale_total"] = sale_item.sale_total

        # always add the key for purchasing price of each item by diving total amount by quantity
        item["purchase_price"] = item["purchase_total"]/item["quantity"]

        # add item in list
        items.append(item)

    # sets context
    context["items"] = items

    return render(request, "index/stock.html", context)


# updates sale price
def update_sale_price(request):

    # checks if user is logged in
    if not authenticated(request):
        return redirect('login')

    # checks whether form is submitted or not
    if request.method == "POST":

        # if pid field empty, return error
        if not request.POST.get("pid"):
            # sets a cookie describing the error
            request.session["i_p"] = 1
            return redirect('stock')
        # if price field empty, return error
        elif not request.POST.get("s_price"):
            # sets a cookie describing the error
            request.session["i_sp"] = 1
            return redirect('stock')

        # checks whether sale price is a valid input
        try:
            s_price = Decimal(request.POST.get("s_price"))
            if s_price < 0:
                # sets a cookie describing the error
                request.session["i_sp"] = 1
                return redirect('stock')
        except InvalidOperation:
            # sets a cookie describing the error
            request.session["i_sp"] = 1
            return redirect('stock')

        # checks whether the item exists in database or not
        try:
            item = Purchase.objects.get(pid=request.POST.get("pid"))
        except ObjectDoesNotExist:
            # sets a cookie describing the error
            request.session["i_p"] = 1
            return redirect('stock')

        # gets it's respective sale columns from database
        s_item = SalePrice.objects.get(pid=item)

        # sets tax variables
        gst = item.percent_gst
        igst = item.percent_igst

        # update records and saves them
        s_item.sale_price = s_price
        s_item.sale_gst = s_price * gst / 100
        s_item.sale_igst = s_price * igst / 100
        s_item.sale_tax = (s_price * gst / 100) + (s_price * igst / 100)
        s_item.sale_total = s_price + (s_price * gst / 100) + (s_price * igst / 100)
        s_item.save()

        # sets a cookie to convey success
        request.session["s_s"] = 1

    return redirect('stock')


# handles purchasing
def purchase(request):
    # checks if user is logged in
    if not authenticated(request):
        return redirect('login')

    # checks if request method is post
    if request.method == "POST":
        # if pid field empty, return error
        if not request.POST.get("pid"):
            return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid PID"})
        # if name field empty, return error
        elif not request.POST.get("name"):
            return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid name"})
        # if vendor field empty, return error
        elif not request.POST.get("vendor"):
            return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid vendor"})
        # if quantity field empty, return error
        elif not request.POST.get("quantity"):
            return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid quantity"})
        # if price field empty, return error
        elif not request.POST.get("price"):
            return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid Price"})
        # if gst field empty, return error
        elif not request.POST.get("percent_gst"):
            return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid GST"})

        # try to convert quantity into int, if error or quantity less 1, return error
        try:
            quantity = int(request.POST.get("quantity"))
            if quantity < 1:
                return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid quantity"})
        except ValueError:
            return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid quantity"})

        # try to convert price into float, if error or price less 0, return error
        try:
            price = Decimal(request.POST.get("price"))
            if price < 0:
                return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid price"})
        except InvalidOperation:
            return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid price"})

        # try to convert gst into float, if error or gst less 0, return error
        try:
            gst = Decimal(request.POST.get("percent_gst"))
            if gst < 0:
                return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid gst"})
        except InvalidOperation:
            return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid gst"})

        # checks if igst is provided
        if request.POST.get("percent_igst"):
            # try to convert igst into float, if error or gst less 0, return error
            try:
                igst = Decimal(request.POST.get("percent_igst"))
                if igst < 0:
                    return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid igst"})
                # calculates igst tax
                igst_tax = igst * price / 100
            except InvalidOperation:
                return render(request, "index/purchase.html", {"authenticated": True, "n_message": "Invalid igst"})
        else:
            # if igst is not provided, assume it to be zero
            igst = Decimal(0)
            igst_tax = Decimal(0)

        # calculates total tax according to quantity
        total_tax = ((price * gst / 100) + igst_tax) * quantity

        # if item already exists, update its record otherwise create new record
        try:
            item = Purchase.objects.get(pid=request.POST.get("pid").replace(" ", ""))
            item.name = request.POST.get("name")
            item.vendor = request.POST.get("vendor")
            item.quantity = item.quantity+quantity
            item.purchase_price = price
            item.percent_gst = gst
            item.percent_cgst = gst / 2
            item.percent_sgst = gst / 2
            item.percent_igst = igst
            item.purchase_gst = price * gst / 100
            item.purchase_igst = igst_tax
            item.total_purchase_tax = total_tax
            item.purchase_total = total_tax + (price * quantity)
            # variable to let database know, this is a new purchase not a change in quantity(sale)
            item._new = True
            item._q = quantity
            item.save()
        except ObjectDoesNotExist:
            item = Purchase(pid=request.POST.get("pid").replace(" ", ""), name=request.POST.get("name"),
                            quantity=quantity, vendor=request.POST.get("vendor"), purchase_price=price, percent_gst=gst,
                            purchase_gst=gst * price / 100, percent_cgst=gst / 2, percent_sgst=gst / 2,
                            percent_igst=igst, purchase_igst=igst_tax, total_purchase_tax=total_tax,
                            purchase_total=(total_tax + (price * quantity)))
            # variable to let database know, this is a new purchase not a change in quantity(sale)
            item._new = True
            item._q = quantity
            item.save()

        # checks if user has provided selling price
        if request.POST.get("s_price"):
            # try to convert gst into float, if error or gst less 0, return error
            try:
                s_price = Decimal(request.POST.get("s_price"))
                if s_price < 0:
                    return render(request, "index/purchase.html", {"authenticated": True,
                                                                   "n_message": "Invalid sale price"})
            except InvalidOperation:
                return render(request, "index/purchase.html", {"authenticated": True, "n_message":
                                                               "Invalid sale price"})

            # creates sales objects and saves it into database
            s_item = SalePrice.objects.get(pid=item)
            s_item.sale_price = s_price
            s_item.sale_gst = s_price * gst / 100
            s_item.sale_igst = s_price * igst / 100
            s_item.sale_tax = (s_price * gst / 100) + (s_price * igst / 100)
            s_item.sale_total = s_price + (s_price * gst / 100) + (s_price * igst / 100)
            s_item.save()

        return render(request, "index/purchase.html", {"authenticated": True, "p_message":
                                                       "Purchase successfully added."})

    return render(request, "index/purchase.html", {"authenticated": True})


# handles buying
def sell(request):

    # checks if user is logged in
    if not authenticated(request):
        return redirect('login')

    if request.method == "POST":
        # if pid field empty, return error
        if not request.POST.get("pid"):
            return render(request, "index/sell.html", {"authenticated": True, "n_message": "Invalid PID"})
        # if customer name field empty, return error
        elif not request.POST.get("customer"):
            return render(request, "index/sell.html", {"authenticated": True, "n_message": "Invalid customer"})
        # if quantity field empty, return error
        elif not request.POST.get("quantity"):
            return render(request, "index/sell.html", {"authenticated": True, "n_message": "Invalid quantity"})

        # checks whether quantity is an integer or not
        try:
            quantity = int(request.POST.get("quantity"))
        except ValueError:
            return render(request, "index/sell.html", {"authenticated": True, "n_message": "Invalid quantity"})

        # checks whether the requested item exists or not
        try:
            item = Purchase.objects.get(pid=request.POST.get("pid"))
            sale_item = SalePrice.objects.get(pid=item)
        except ObjectDoesNotExist:
            return render(request, "index/sell.html", {"authenticated": True, "n_message": "Invalid PID"})

        # if the item's sale price is not added, return error
        if sale_item.sale_price is None:
            return render(request, "index/sell.html", {"authenticated": True, "n_message": "Product not for sale."})

        # if the quantity requested is more than available quantity, return error
        if quantity > item.quantity:
            return render(request, "index/sell.html", {"authenticated": True, "n_message":
                                                       "Requested quantity more than available quantity."})

        # makes a buyer object and saves it into database
        s_price = sale_item.sale_price
        gst = item.percent_gst
        igst = item.percent_igst
        tax = ((gst*s_price/100) + (igst*s_price/100))*quantity
        total = tax+s_price*quantity
        buyer = Buyer(pid=item, name=request.POST.get("customer"), quantity=quantity, sale_price=s_price, sale_gst=
                      (gst*s_price/100), sale_igst=(igst*s_price/100), sale_tax=tax, sale_total=total)
        buyer.save()

        # updates the quantity of item in Purchase database
        item.quantity = item.quantity - quantity
        # variable to tell database this is not a purchase
        item._new = False
        item._q = 0
        item.save()

        return render(request, "index/sell.html", {"authenticated": True, "p_message": "Product sold successfully"})

    pid_list = Purchase.objects.all().values_list('pid', flat=True)

    return render(request, "index/sell.html", {"authenticated": True, "pid_list": pid_list})


# handles pdf
def invoice(request):
    if not authenticated(request):
        return redirect('login')

    template = "index/test.html"
    context = {}

    response = render_to_pdf("invoice", template, context)

    return response


# item list
def item_list(request):
    # checks whether user is logged in or not
    if not authenticated(request):
        return redirect('login')

    # gets all the records from database
    items = Purchase.objects.all()

    # sets template to use for generation of pdf
    template = "index/item_list.html"

    # calls pdf generation function, passing in template and context, getting pdf in return
    response = render_to_pdf("item_list", template, {"items": items})

    # displays pdf
    return response


# generates report
def report(request):
    # checks if user is authenticated
    if not authenticated(request):
        return redirect('login')

    # if form is submitted
    if request.method == "POST":
        if not request.POST.get("choice"):
            return render(request, "index/generate_report.html", {"authenticated": True, "n_message": "Please select "
                                                                                                      "a choice"})
        elif not request.POST.get("to"):
            return render(request, "index/generate_report.html", {"authenticated": True, "n_message": "Please enter a "
                                                                                                      "'to' date."})
        elif not request.POST.get("from"):
            return render(request, "index/generate_report.html", {"authenticated": True, "n_message": "Please enter a "
                                                                                                      "'from' date."})
        elif not request.POST.get("type"):
            return render(request, "index/generate_report.html", {"authenticated": True, "n_message": "Please select "
                                                                                                      "a type"})
        # try to check whether date is in valid format or not
        try:
            from_date = request.POST.get("from")
            # makes sure that 'from' date starts when the day starts
            from_date += " 00:00:00"
            from_date = datetime.strptime(from_date, "%d/%m/%Y %H:%M:%S")
        except ValueError:
            return render(request, "index/generate_report.html", {"authenticated": True, "n_message": "Invalid Date"})

        # try to check whether date is in valid format or not
        try:
            to_date = request.POST.get("to")
            # makes sure that 'to' date ends when the day ends
            to_date += " 23:59:59"
            to_date = datetime.strptime(to_date, "%d/%m/%Y %H:%M:%S")
        except ValueError:
            return render(request, "index/generate_report.html", {"authenticated": True, "n_message": "Invalid Date"})

        # if 'to' date is earlier than 'from' date, return error
        if (to_date - from_date).days < 0:
            return render(request, "index/generate_report.html", {"authenticated": True, "n_message": "Invalid Date"})

        # if user asks for both purchase and sale transactions
        if request.POST.get("choice") == "both":

            # variables to hold calculations
            buy = 0
            sale = 0

            # retrieves queryset from database in the requested parameter
            qs = Transaction.objects.filter(datetime__range=[from_date, to_date])
            items = []

            # if queryset empty, return error
            if not qs.exists():
                return render(request, "index/report.html", {"authenticated": True, "n_message": "No data found."})

            # enumerate through queryset
            for transaction in qs:
                # convert model object to dict
                item = model_to_dict(transaction)

                # if transaction is of 'purchase' type, negate its price and tax
                if transaction.type == 'purchase':
                    buy = buy - transaction.total
                    item["tax"] = "-{}".format(transaction.tax)
                    item["total"] = "-{}".format(transaction.total)

                    # makes sure that pid itself is printed instead of id of pid
                    item["pid"] = str(transaction.pid)
                else:
                    sale = sale + transaction.total
                    item["pid"] = str(transaction.pid)
                items.append(item)

            # to tell user - average profit or average sale
            average = buy + sale

            # if user asks for pdf, set the template and call respective function
            if request.POST.get("type") == "pdf":
                template = "index/generate_report.html"
                response = render_to_pdf("report", template, {"items": items, "average": average, "buy": buy, "sale": sale,
                                                    "heading": "Sale and Purchase from {} to {}".format
                                                    (str(from_date).split(" ", 1)[0], str(to_date).split(" ", 1)[0])})
            # if user asks for excel, call respective function
            elif request.POST.get("type") == "excel":
                response = write_to_excel("Sale and Purchase", str(from_date).split(" ", 1)[0],
                                          str(to_date).split(" ", 1)[0], qs)
            # if type is neither pdf nor excel, redirect to report
            else:
                return redirect('report')

            return response

        # if user asks for only purchase objects
        elif request.POST.get("choice") == "purchase":

            # variable to hold sum of all purchase totals
            buy = 0

            # retrieves queryset from database in the requested parameter
            qs = Transaction.objects.filter(datetime__range=[from_date, to_date], type='purchase')

            # if queryset is empty, return error
            if not qs.exists():
                return render(request, "index/report.html", {"authenticated": True, "n_message": "No data found."})

            for transaction in qs:
                buy += transaction.total

            # if user asks for pdf, set the template and call respective function
            if request.POST.get("type") == "pdf":
                template = "index/generate_report.html"
                response = render_to_pdf("report", template, {"items": qs, "buy": buy, "heading": "Purchase from {} to {}".format
                                                    (str(from_date).split(" ", 1)[0], str(to_date).split(" ", 1)[0])})
            # if user asks for excel, set the template and call respective function
            elif request.POST.get("type") == "excel":
                response = write_to_excel("Purchase", str(from_date).split(" ", 1)[0],
                                          str(to_date).split(" ", 1)[0], qs)
            else:
                return redirect('report')

            return response

        # if user asks for only sale transaction
        elif request.POST.get("choice") == "sale":

            # variable to hold sum of all sales
            sale = 0

            # retrieves queryset from database in the requested parameter
            qs = Transaction.objects.filter(datetime__range=[from_date, to_date], type='sale')

            # if queryset is empty, return error
            if not qs.exists():
                return render(request, "index/report.html", {"authenticated": True, "n_message": "No data found."})

            for transaction in qs:
                sale += transaction.total

            # if user asks for pdf, set the template and call respective function
            if request.POST.get("type") == "pdf":
                template = "index/generate_report.html"
                response = render_to_pdf("report", template, {"items": qs, "sale": sale, "heading": "Sale from {} to {}".format
                                                    (str(from_date).split(" ", 1)[0], str(to_date).split(" ", 1)[0])})
            # if user asks for excel, set the template and call respective function
            elif request.POST.get("type") == "excel":
                response = write_to_excel("Sale", str(from_date).split(" ", 1)[0],
                                          str(to_date).split(" ", 1)[0], qs)
            else:
                return redirect('report')

            return response

    return render(request, "index/report.html", {"authenticated": True})


# checks if user is logged in
def authenticated(request):
    try:
        request.session["user_id"]
    except KeyError:
        return False
    return True


# handles ajax request to validate pid(SELL)
def validate_pid(request):
    # gets product id from url
    pid = request.GET.get('pid', None)

    data = {
        'exists': False
    }

    # if pid is not None
    if pid is not None:
        try:
            # if product exists sends back it's data
            item = Purchase.objects.get(pid=pid.replace(" ", ""))
            sale_item = SalePrice.objects.get(pid=item)

            # checks if product is for sale or not
            if sale_item.sale_price is None:
                data = {
                    'exists': False
                }
            else:
                data = {
                    'exists': True,
                    'name': item.name,
                    'price': sale_item.sale_price,
                    'available': item.quantity,
                    'gst': item.percent_gst,
                    'igst': item.percent_igst,
                    'price_gst': sale_item.sale_gst,
                    'price_igst': sale_item.sale_igst,
                }
        except ObjectDoesNotExist:
            data = {
                'exists': False
            }

    return JsonResponse(data)


# handles ajax request to check for pid data(BUY)
def pid_check(request):
    # gets product id from url
    pid = request.GET.get('pid', None)

    data = {
        'exists': False
    }

    if pid is not None:
        try:
            # if product exists sends back it's data
            item = Purchase.objects.get(pid=pid.replace(" ", ""))
            sale_item = SalePrice.objects.get(pid=item)

            data = {
                'exists': True,
                'name': item.name,
                'vendor': item.vendor,
                'p_gst': item.percent_gst,
                'p_igst': item.percent_igst,
            }

            if sale_item.sale_price is not None:
                data = {
                    'exists': True,
                    'name': item.name,
                    'vendor': item.vendor,
                    'p_gst': item.percent_gst,
                    'p_igst': item.percent_igst,
                    's_price': sale_item.sale_price,
                }
        except ObjectDoesNotExist:
            pass

    return JsonResponse(data)


# handles ajax request to check for different purchases(same PID)
def get_vendors(request):
    # gets product id from url
    pid = request.GET.get('pid', None)

    data = []

    if pid is not None:
        try:
            # if product exists sends back it's data
            item = Purchase.objects.get(pid=pid.replace(" ", ""))
            vendors = Transaction.objects.filter(pid=item)
            records = []
            for vendor in vendors:
                row = dict()
                if vendor.type == 'purchase':
                    row["vendor"] = vendor.name
                    row["quantity"] = vendor.quantity
                    row["price"] = vendor.total / vendor.quantity
                    date = str(localtime(vendor.datetime)).split(".", 1)[0]
                    row["datetime"] = date
                    records.append(row)

            data = records

        except ObjectDoesNotExist:
            pass

    return JsonResponse(data, safe=False)
