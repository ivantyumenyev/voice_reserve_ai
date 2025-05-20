from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel


class Reservation(BaseModel):
    """Reservation model."""
    reservation_id: str
    date: datetime
    party_size: int
    customer_name: str
    phone_number: str
    status: str = "confirmed"


class ReservationCalendar:
    """Calendar for managing restaurant reservations."""
    
    def __init__(self):
        self.reservations: Dict[str, Reservation] = {}
    
    def add_reservation(
        self,
        date: datetime,
        party_size: int,
        customer_name: str,
        phone_number: str
    ) -> Reservation:
        """Add a new reservation to the calendar."""
        reservation_id = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        reservation = Reservation(
            reservation_id=reservation_id,
            date=date,
            party_size=party_size,
            customer_name=customer_name,
            phone_number=phone_number
        )
        
        self.reservations[reservation_id] = reservation
        return reservation
    
    def get_reservation(self, reservation_id: str) -> Optional[Reservation]:
        """Get a reservation by ID."""
        return self.reservations.get(reservation_id)
    
    def cancel_reservation(self, reservation_id: str) -> bool:
        """Cancel a reservation."""
        if reservation_id in self.reservations:
            self.reservations[reservation_id].status = "cancelled"
            return True
        return False
    
    def get_available_times(
        self,
        date: datetime,
        party_size: int
    ) -> List[str]:
        """Get available reservation times for a given date and party size."""
        # TODO: Implement actual availability checking logic
        # This is a placeholder implementation
        return [
            "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
            "18:00", "18:30", "19:00", "19:30", "20:00", "20:30"
        ]
    
    def check_availability(
        self,
        date: datetime,
        time: str,
        party_size: int
    ) -> bool:
        """Check if a specific time slot is available."""
        # TODO: Implement actual availability checking logic
        # This is a placeholder implementation
        return True 