from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Category, Product, Artist, Order, OrderItem, UserSubmission, CustomizedPainting
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.mail import send_mail
from django.conf import settings
from .forms import ProductForm, ArtistUpdateForm
from django.db.models import Q
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import base64

def home(request):
    categories = Category.objects.all()[:3]  # Get first 3 categories
    featured_products = Product.objects.filter(is_featured=True)[:4]  # Get 4 featured products
    featured_artists = Artist.objects.filter(is_featured=True)[:3]  # Get 3 featured artists
    recent_submissions = UserSubmission.objects.filter(is_approved=True).order_by('-created_at')[:6]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'featured_artists': featured_artists,
        'recent_submissions': recent_submissions
    }
    return render(request, 'paintingapp/home.html', context)

def about(request):
    return render(request, 'paintingapp/about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Send email
        email_message = f"""
        Name: {name}
        Email: {email}
        Subject: {subject}
        Message:
        {message}
        """
        
        try:
            send_mail(
                f'Contact Form: {subject}',
                email_message,
                email,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
        except Exception as e:
            messages.error(request, 'There was an error sending your message. Please try again later.')
    
    return render(request, 'paintingapp/contact.html')

class CategoryListView(ListView):
    model = Category
    template_name = 'paintingapp/category_list.html'
    context_object_name = 'categories'

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'paintingapp/category_detail.html'
    context_object_name = 'category'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products_list = Product.objects.filter(category=self.object)
        paginator = Paginator(products_list, self.paginate_by)
        page = self.request.GET.get('page')
        products = paginator.get_page(page)
        context['products'] = products
        context['page_obj'] = products
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'paintingapp/product_detail.html'
    context_object_name = 'product'

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if product.stock <= 0:
        messages.error(request, 'Sorry, this product is out of stock.')
        return redirect('product_detail', pk=product_id)
    
    cart = request.session.get('cart', {})
    
    if str(product_id) in cart:
        if cart[str(product_id)] < product.stock:
            cart[str(product_id)] += 1
        else:
            messages.warning(request, f'Sorry, only {product.stock} pieces available.')
            return redirect('product_detail', pk=product_id)
    else:
        cart[str(product_id)] = 1
    
    request.session['cart'] = cart
    messages.success(request, f'{product.name} added to cart!')
    return redirect('product_detail', pk=product_id)

@login_required
def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = 0
    shipping = 50  # Fixed shipping cost
    
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        item_total = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': item_total
        })
        subtotal += item_total
    
    total = subtotal + shipping
    
    return render(request, 'paintingapp/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total
    })

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('view_cart')
    
    cart_items = []
    subtotal = 0
    
    # Process cart items
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        item_total = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': item_total
        })
        subtotal += item_total
    
    shipping = 100  # Fixed shipping cost
    total = subtotal + shipping
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total
    }
    return render(request, 'paintingapp/checkout.html', context)

@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            # Get cart items from session
            cart = request.session.get('cart', {})
            if not cart:
                messages.error(request, 'Your cart is empty')
                return redirect('view_cart')

            # Calculate totals
            subtotal = 0
            shipping_cost = 100  # Fixed shipping cost
            cart_items = []

            for product_id, quantity in cart.items():
                product = get_object_or_404(Product, id=product_id)
                item_total = product.price * quantity
                subtotal += item_total
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': item_total
                })

            total_amount = subtotal + shipping_cost

            # Create order
            order = Order.objects.create(
                user=request.user,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                pincode=request.POST.get('pincode'),
                payment_method=request.POST.get('payment_method', 'COD'),
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                total_amount=total_amount,
                status='pending'
            )

            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['product'].price
                )

            # Clear cart
            request.session['cart'] = {}

            # Redirect to order confirmation
            return redirect('order_confirmation', order_id=order.id)

        except Exception as e:
            messages.error(request, f'Error placing order: {str(e)}')
            return redirect('checkout')

    return redirect('checkout')

@login_required
def order_confirmation(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        return render(request, 'paintingapp/order_confirmation.html', {'order': order})
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('order_history')
    except Exception as e:
        messages.error(request, 'An error occurred while retrieving your order.')
        return redirect('order_history')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'paintingapp/order_history.html', {'orders': orders})

class ArtistCreateView(LoginRequiredMixin, CreateView):
    model = Artist
    template_name = 'paintingapp/artist_form.html'
    fields = ['name', 'profession', 'bio', 'profile_picture']
    success_url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        # Check if user already has an artist profile
        if hasattr(request.user, 'artist'):
            messages.info(request, 'You already have an artist profile. You can update it instead.')
            return redirect('artist_update', pk=request.user.artist.id)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # Check if user already has an artist profile
        if hasattr(self.request.user, 'artist'):
            messages.error(self.request, 'You already have an artist profile.')
            return redirect('artist_update', pk=self.request.user.artist.id)
        
        form.instance.user = self.request.user
        return super().form_valid(form)

class ArtistUpdateView(LoginRequiredMixin, UpdateView):
    model = Artist
    form_class = ProductForm
    template_name = 'paintingapp/artist_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(artist=self.object)
        return context

    def form_valid(self, form):
        product = form.save(commit=False)
        product.artist = self.object
        product.price = 0
        product.stock = 0
        product.save()
        messages.success(self.request, 'Artwork shared successfully!')
        return redirect('artist_update', pk=self.object.pk)

    def get_success_url(self):
        return reverse('artist_update', kwargs={'pk': self.object.pk})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to Painting Store.')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'paintingapp/signup.html', {'form': form})

class ArtistListView(ListView):
    model = Artist
    template_name = 'paintingapp/artist_list.html'
    context_object_name = 'artists'
    paginate_by = 12

class ArtistDetailView(DetailView):
    model = Artist
    template_name = 'paintingapp/artist_detail.html'
    context_object_name = 'artist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(artist=self.object)
        return context

@login_required
def add_painting(request, artist_id):
    artist = get_object_or_404(Artist, id=artist_id)
    
    # Check if the logged-in user is the artist
    if request.user != artist.user:
        messages.error(request, 'You are not authorized to add paintings for this artist.')
        return redirect('artist_detail', pk=artist_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.artist = artist
            product.price = 0  # Set default price
            product.stock = 0  # Set default stock
            product.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Return JSON response for AJAX request
                return JsonResponse({
                    'success': True,
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'description': product.description,
                        'image_url': product.image.url,
                        'detail_url': reverse('product_detail', kwargs={'pk': product.pk})
                    }
                })
            else:
                messages.success(request, 'Painting added successfully!')
                return redirect('artist_update', pk=artist_id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    
    return redirect('artist_update', pk=artist_id)

def search(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'newest')
    page = request.GET.get('page', 1)
    
    # Base queryset
    results = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(artist__name__icontains=query) |
        Q(category__name__icontains=query)
    )
    
    # Apply sorting
    if sort_by == 'newest':
        results = results.order_by('-created_at')
    elif sort_by == 'oldest':
        results = results.order_by('created_at')
    elif sort_by == 'price_high':
        results = results.order_by('-price')
    elif sort_by == 'price_low':
        results = results.order_by('price')
    
    # Pagination
    paginator = Paginator(results, 12)  # Show 12 items per page
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)
    
    context = {
        'query': query,
        'results': results,
        'results_count': paginator.count,
    }
    
    return render(request, 'paintingapp/search_results.html', context)

@login_required
def update_cart(request, product_id):
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            product = get_object_or_404(Product, id=product_id)
            
            cart = request.session.get('cart', {})
            
            if quantity > 0 and quantity <= product.stock:
                cart[str(product_id)] = quantity
                request.session['cart'] = cart
                return JsonResponse({
                    'success': True,
                    'message': f'Quantity updated for {product.name}'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid quantity. Maximum available: {product.stock}'
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)

@login_required
def remove_from_cart(request, product_id):
    if request.method == 'POST':
        try:
            cart = request.session.get('cart', {})
            product = get_object_or_404(Product, id=product_id)
            
            if str(product_id) in cart:
                del cart[str(product_id)]
                request.session['cart'] = cart
                return JsonResponse({
                    'success': True,
                    'message': f'{product.name} removed from cart'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Item not found in cart'
                }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)

@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        query = request.POST.get('query', '').lower()
        response = {
            'status': 'success',
            'message': '',
            'data': []
        }
        
        try:
            # Check for common painting-related keywords
            if any(word in query for word in ['paintings', 'artworks', 'art pieces']):
                paintings = Product.objects.all()[:5]  # Get 5 recent paintings
                response['message'] = 'Here are some of our recent paintings:'
                response['data'] = [{
                    'type': 'painting',
                    'name': p.name,
                    'artist': p.artist.name,
                    'price': p.price,
                    'image': p.image.url if p.image else None,
                    'url': reverse('product_detail', args=[p.id]),
                    'category': p.category.name,
                    'stock': p.stock
                } for p in paintings]
                
            elif 'artist' in query:
                artists = Artist.objects.all()[:5]  # Get 5 artists
                response['message'] = 'Here are some of our talented artists:'
                response['data'] = [{
                    'type': 'artist',
                    'name': a.name,
                    'profession': a.profession,
                    'image': a.profile_picture.url if a.profile_picture else None,
                    'url': reverse('artist_detail', args=[a.id]),
                    'paintings_count': a.products.count()
                } for a in artists]
                
            elif 'category' in query or 'type' in query:
                categories = Category.objects.all()
                response['message'] = 'We have paintings in these categories:'
                response['data'] = [{
                    'type': 'category',
                    'name': c.name,
                    'count': c.products.count(),
                    'url': reverse('category_detail', args=[c.id]),
                    'artists_count': len(set(c.products.values_list('artist', flat=True)))
                } for c in categories]
                
            elif 'price' in query or 'cost' in query:
                # Get price range information
                min_price = Product.objects.aggregate(min_price=models.Min('price'))['min_price']
                max_price = Product.objects.aggregate(max_price=models.Max('price'))['max_price']
                avg_price = Product.objects.aggregate(avg_price=models.Avg('price'))['avg_price']
                
                response['message'] = f'Our paintings range from ₹{min_price} to ₹{max_price}.'
                response['data'] = [{
                    'type': 'price_info',
                    'min_price': min_price,
                    'max_price': max_price,
                    'avg_price': round(avg_price, 2)
                }]
                
            else:
                response['message'] = 'I can help you with information about paintings, artists, categories, and prices. What would you like to know?'
            
            return JsonResponse(response)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Sorry, I encountered an error. Please try again.'
            })
    
    return render(request, 'paintingapp/chatbot.html')

@csrf_exempt
@require_POST
def submit_drawing(request):
    try:
        name = request.POST.get('name')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        
        if not all([name, description, image]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
            
        # Create a new UserSubmission instance
        submission = UserSubmission(
            name=name,
            description=description,
            artist=request.user if request.user.is_authenticated else None,
            image=image,
            is_approved=True  # Set to True for testing
        )
        
        submission.save()
        
        return JsonResponse({
            'success': True,
            'submission': {
                'id': submission.id,
                'name': submission.name,
                'description': submission.description,
                'image_url': submission.image.url if submission.image else None,
                'artist': submission.artist.username if submission.artist else 'Anonymous',
                'created_at': submission.created_at.strftime('%B %d, %Y')
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def user_submissions(request):
    submissions = UserSubmission.objects.filter(is_approved=True).order_by('-created_at')
    return render(request, 'paintingapp/user_submissions.html', {
        'submissions': submissions
    })

def charity(request):
    return render(request, 'paintingapp/charity.html')

def customize(request):
    return render(request, 'paintingapp/customize.html')

@login_required
def save_customized_painting(request):
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            style = request.POST.get('style', '').strip()
            size = request.POST.get('size', '').strip()
            frame = request.POST.get('frame', '').strip()
            image = request.FILES.get('image')

            # Debug print
            print(f"Received data: title={title}, style={style}, size={size}, frame={frame}")
            print(f"Image received: {image is not None}")

            # Validate required fields
            if not title:
                return JsonResponse({'success': False, 'error': 'Title is required'})
            if not description:
                return JsonResponse({'success': False, 'error': 'Description is required'})
            if not style:
                return JsonResponse({'success': False, 'error': 'Please select an art style'})
            if not size:
                return JsonResponse({'success': False, 'error': 'Please select a canvas size'})
            if not frame:
                return JsonResponse({'success': False, 'error': 'Please select a frame style'})
            if not image:
                return JsonResponse({'success': False, 'error': 'Please upload an image'})

            # Validate image file
            if not image.content_type.startswith('image/'):
                return JsonResponse({'success': False, 'error': 'Please upload a valid image file'})

            try:
                # Create a new CustomizedPainting instance
                customized_painting = CustomizedPainting(
                    user=request.user,
                    title=title,
                    description=description,
                    style=style,
                    size=size,
                    frame=frame,
                    image=image
                )
                customized_painting.save()

                # Return success response
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('customized_painting_detail', args=[customized_painting.id])
                })

            except Exception as e:
                print(f"Error saving painting: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error saving painting: {str(e)}'
                })

        except Exception as e:
            print(f"Error in save_customized_painting: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'An error occurred: {str(e)}'
            })

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def customized_painting_detail(request, pk):
    painting = get_object_or_404(CustomizedPainting, id=pk, user=request.user)
    return render(request, 'paintingapp/customized_painting_detail.html', {
        'painting': painting
    })