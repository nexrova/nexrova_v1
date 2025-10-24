"""
Web interface routes for Hotel PMS
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from database.models import (
    RoomModel, BookingModel, GuestModel, OccupancyModel
)
from config import Config
import logging

logger = logging.getLogger(__name__)

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html', hotel=Config.HOTEL_INFO)

@web_bp.route('/dashboard')
def dashboard():
    """Admin dashboard with statistics"""
    try:
        stats = OccupancyModel.get_stats()
        checked_in_guests = GuestModel.get_checked_in_guests()
        return render_template(
            'dashboard.html',
            occupancy_rate=stats['occupancy_rate'],
            total_rooms=stats['total_rooms'],
            occupied_rooms=stats['occupied_rooms'],
            available_rooms=stats['available_rooms'],
            maintenance_rooms=stats['maintenance_rooms'],
            check_ins=stats['check_ins_today'],
            check_outs=stats['check_outs_today'],
            checked_in_guests=checked_in_guests,
            hotel=Config.HOTEL_INFO
        )
    except Exception as e:
        logger.error(f"Error in dashboard: {e}")
        flash("Error loading dashboard data", "error")
        return render_template(
            'dashboard.html',
            occupancy_rate=0,
            total_rooms=0,
            occupied_rooms=0,
            available_rooms=0,
            maintenance_rooms=0,
            check_ins=0,
            check_outs=0,
            checked_in_guests=[],
            hotel=Config.HOTEL_INFO
        )

@web_bp.route('/rooms')
def rooms():
    """Room management page"""
    try:
        rooms_with_guests = RoomModel.get_all_with_guest_details()
        return render_template('rooms.html', rooms=rooms_with_guests, hotel=Config.HOTEL_INFO)
    except Exception as e:
        logger.error(f"Error loading rooms: {e}")
        flash("Error loading rooms data", "error")
        return render_template('rooms.html', rooms=[], hotel=Config.HOTEL_INFO)

@web_bp.route('/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
def edit_room(room_id):
    """Edit room details"""
    room = RoomModel.get_by_id(room_id)
    if not room:
        return "Room not found", 404
    if request.method == 'POST':
        new_status = request.form.get('status')
        new_price = request.form.get('base_price')
        update_data = {}
        if new_status in ['available', 'occupied', 'maintenance']:
            update_data['status'] = new_status
        if new_price:
            try:
                update_data['base_price'] = float(new_price)
            except ValueError:
                pass
        if update_data:
            RoomModel.update(room_id, update_data)
        return redirect(url_for('web.rooms'))
    return render_template('edit_room.html', room=room, hotel=Config.HOTEL_INFO)

@web_bp.route('/bookings')
def bookings():
    """Bookings management page"""
    try:
        enriched_bookings = BookingModel.get_all_enriched()
        return render_template('bookings.html', bookings=enriched_bookings, hotel=Config.HOTEL_INFO)
    except Exception as e:
        logger.error(f"Error loading bookings: {e}")
        flash("Error loading bookings data", "error")
        return render_template('bookings.html', bookings=[], hotel=Config.HOTEL_INFO)

@web_bp.route('/bookings/update-status/<int:booking_id>/<status>')
def update_booking_status_route(booking_id, status):
    """Update booking status"""
    if status in ['confirmed', 'checked_in', 'checked_out', 'cancelled']:
        BookingModel.update_status(booking_id, status)
    return redirect(url_for('web.bookings'))

@web_bp.route('/new-booking', methods=['GET', 'POST'])
def new_booking():
    """Create new booking"""
    if request.method == 'POST':
        try:
            # Create guest
            guest_data = {
                'name': request.form['guest_name'],
                'email': request.form['guest_email'],
                'phone': request.form['guest_phone'],
                'id_proof': request.form.get('id_proof', '')
            }
            guest = GuestModel.create(guest_data)
            
            # Calculate total price
            check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d')
            check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d')
            nights = (check_out - check_in).days
            room_id = int(request.form['room_id'])
            room = RoomModel.get_by_id(room_id)
            total_price = float(room['base_price']) * nights
            
            # Create booking
            booking_data = {
                'room_id': room_id,
                'guest_id': guest['guest_id'],
                'check_in': request.form['check_in'],
                'check_out': request.form['check_out'],
                'total_price': total_price
            }
            BookingModel.create(booking_data)
            flash("Booking created successfully!", "success")
            return redirect(url_for('web.bookings'))
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            flash("Error creating booking. Please try again.", "error")
    
    # Get available rooms
    try:
        available_rooms = [r for r in RoomModel.get_all() if r['status'] == 'available']
    except Exception as e:
        logger.error(f"Error loading rooms: {e}")
        available_rooms = []
    
    return render_template('new_booking.html', rooms=available_rooms, hotel=Config.HOTEL_INFO)

@web_bp.route('/guests')
def guests_page():
    """Guest management page"""
    try:
        guests_with_details = GuestModel.get_all_with_booking_details()
        return render_template('guests.html', guests=guests_with_details, hotel=Config.HOTEL_INFO)
    except Exception as e:
        logger.error(f"Error loading guests: {e}")
        flash("Error loading guests data", "error")
        return render_template('guests.html', guests=[], hotel=Config.HOTEL_INFO)