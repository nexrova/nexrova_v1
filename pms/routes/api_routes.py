from flask import Blueprint, jsonify, request
from datetime import datetime
from database.models import (
RoomModel, BookingModel, GuestModel, OccupancyModel
)
from config import Config
api_bp = Blueprint('api', __name__)

@api_bp.route('/hotel-info', methods=['GET'])
def api_hotel_info():
    # Get hotel information
    return jsonify({
        'success': True,
        'data': Config.HOTEL_INFO
    })

@api_bp.route('/rooms', methods=['GET'])
def api_rooms():
    # Get all rooms with guest information
    rooms = RoomModel.get_all_with_guest_details()
    return jsonify({
        'success': True,
        'data': rooms
    })

@api_bp.route('/rooms/<int:room_id>', methods=['GET', 'PUT'])
def api_room_detail(room_id):
    # Get or update specific room
    room = RoomModel.get_with_guest_details(room_id)
    if not room:
        return jsonify({
            'success': False,
            'error': 'Room not found'
        }), 404
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': room
        })
    if request.method == 'PUT':
        data = request.get_json()
        update_data = {}
        if 'status' in data:
            if data['status'] not in ['available', 'occupied', 'maintenance']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid status'
                }), 400
            update_data['status'] = data['status']
        if 'base_price' in data:
            try:
                price = float(data['base_price'])
                if price <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Price must be greater than 0'
                    }), 400
                update_data['base_price'] = price
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid price format'
                }), 400
        if update_data:
            RoomModel.update(room_id, update_data)
            updated_room = RoomModel.get_with_guest_details(room_id)
            return jsonify({
                'success': True,
                'data': updated_room,
                'message': 'Room updated successfully'
            })

@api_bp.route('/rooms/<int:room_id>/guest', methods=['GET'])
def api_room_current_guest(room_id):
    # Get current guest in room
    room = RoomModel.get_with_guest_details(room_id)
    if not room:
        return jsonify({
            'success': False,
            'error': 'Room not found'
        }), 404
    if room.get('current_guest'):
        return jsonify({
            'success': True,
            'data': room['current_guest']
        })
    else:
        return jsonify({
            'success': True,
            'data': None,
            'message': 'No guest currently checked in'
        })

@api_bp.route('/rooms/available', methods=['GET'])
def api_available_rooms():
    # Get available rooms for dates
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    if not check_in or not check_out:
        return jsonify({
            'success': False,
            'error': 'check_in and check_out dates required'
        }), 400
    try:
        available = RoomModel.get_available_rooms(check_in, check_out)
        return jsonify({
            'success': True,
            'data': available
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'Invalid date format'
        }), 400

@api_bp.route('/bookings', methods=['GET', 'POST'])
def api_bookings():
    # Get all bookings or create new
    if request.method == 'GET':
        bookings = BookingModel.get_all_enriched()
        return jsonify({
            'success': True,
            'data': bookings
        })
    if request.method == 'POST':
        data = request.get_json()
        required = ['room_id', 'guest_name', 'guest_email', 'guest_phone', 'check_in', 'check_out']
        if not all(field in data for field in required):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        room = RoomModel.get_by_id(data['room_id'])
        if not room:
            return jsonify({
                'success': False,
                'error': 'Room not found'
            }), 404
        if not RoomModel.check_availability(data['room_id'], data['check_in'], data['check_out']):
            return jsonify({
                'success': False,
                'error': 'Room not available for selected dates'
            }), 400
        # Create guest
        guest_data = {
            'name': data['guest_name'],
            'email': data['guest_email'],
            'phone': data['guest_phone'],
            'id_proof': data.get('id_proof', '')
        }
        guest = GuestModel.create(guest_data)
        # Calculate price
        try:
            check_in = datetime.strptime(data['check_in'], '%Y-%m-%d')
            check_out = datetime.strptime(data['check_out'], '%Y-%m-%d')
            nights = (check_out - check_in).days
            if nights <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Check-out must be after check-in'
                }), 400
            total_price = float(room['base_price']) * nights
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format'
            }), 400
        # Create booking
        booking_data = {
            'room_id': data['room_id'],
            'guest_id': guest['guest_id'],
            'check_in': data['check_in'],
            'check_out': data['check_out'],
            'total_price': total_price
        }
        booking = BookingModel.create(booking_data)
        return jsonify({
            'success': True,
            'data': booking
        }), 201

@api_bp.route('/bookings/<int:booking_id>', methods=['GET', 'PUT', 'DELETE'])
def api_booking_detail(booking_id):
    # Get, update, or cancel booking
    booking = BookingModel.get_enriched(booking_id)
    if not booking:
        return jsonify({
            'success': False,
            'error': 'Booking not found'
        }), 404
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': booking
        })
    if request.method == 'PUT':
        data = request.get_json()
        if 'status' in data:
            if data['status'] not in ['confirmed', 'checked_in', 'checked_out', 'cancelled']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid status'
                }), 400
            BookingModel.update_status(booking_id, data['status'])
            updated_booking = BookingModel.get_enriched(booking_id)
            return jsonify({
                'success': True,
                'data': updated_booking,
                'message': 'Booking updated successfully'
            })
        return jsonify({
            'success': False,
            'error': 'No valid fields to update'
        }), 400
    if request.method == 'DELETE':
        BookingModel.update_status(booking_id, 'cancelled')
        return jsonify({
            'success': True,
            'message': 'Booking cancelled'
        })

@api_bp.route('/guests', methods=['GET'])
def api_guests():
    # Get all guests
    guests = GuestModel.get_all_with_booking_details()
    return jsonify({
        'success': True,
        'data': guests
    })

@api_bp.route('/guests/<int:guest_id>', methods=['GET'])
def api_guest_detail(guest_id):
    # Get guest details
    guest = GuestModel.get_with_booking_details(guest_id)
    if not guest:
        return jsonify({
            'success': False,
            'error': 'Guest not found'
        }), 404
    return jsonify({
        'success': True,
        'data': guest
    })

@api_bp.route('/guests/checked-in', methods=['GET'])
def api_checked_in_guests():
    # Get checked-in guests
    checked_in = GuestModel.get_checked_in_guests()
    return jsonify({
        'success': True,
        'data': checked_in
    })

@api_bp.route('/occupancy', methods=['GET'])
def api_occupancy():
    # Get occupancy statistics
    stats = OccupancyModel.get_stats()
    return jsonify({
        'success': True,
        'data': stats
    })