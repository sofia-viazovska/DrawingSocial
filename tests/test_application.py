from unittest.mock import MagicMock
import pytest
from app.application.use_cases.services import DrawingUseCases
from app.domain.models.models import Drawing

def test_create_drawing_use_case():
    drawing_repo = MagicMock()
    factory = MagicMock()
    
    drawing_to_save = Drawing(None, 1, "My Art")
    saved_drawing = Drawing(10, 1, "My Art")
    
    factory.create_drawing.return_value = drawing_to_save
    drawing_repo.save.return_value = saved_drawing
    
    services = DrawingUseCases(drawing_repo, factory)
    result = services.create_drawing(1, "My Art")
    
    assert result.id == 10
    drawing_repo.save.assert_called_once_with(drawing_to_save)

def test_add_layer_use_case():
    drawing_repo = MagicMock()
    factory = MagicMock()
    
    drawing = Drawing(1, 1, "My Art")
    drawing_repo.get_by_id.return_value = drawing
    
    services = DrawingUseCases(drawing_repo, factory)
    services.add_layer(1, 1, "base64data")
    
    assert len(drawing.layers) == 1
    assert drawing.layers[0].image_data == "base64data"
    drawing_repo.add_layer.assert_called_once()
