from django.urls import path
from . import views

app_name = 'simulator'

urlpatterns = [
    # Landing and Authentication
    path('', views.landing_page, name='landing_page'),
    path('guide/', views.user_guide, name='user_guide'),
    path('test-storage/', views.test_storage, name='test_storage'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Simulation Pages (Protected)
    path('simulation/', views.main_simulation, name='main_simulation'),
    path('user-manual/', views.user_manual, name='user_manual'),
    path('landuse/', views.landuse_list, name='landuse_list'),
    path('landuse/<int:pk>/update_percent/', views.update_landuse_percent, name='update_landuse_percent'),
    path('landuse/<int:pk>/', views.landuse_detail, name='landuse_detail'),
    path('renewable/', views.renewable_list, name='renewable_list'),
    path('verbrauch/', views.verbrauch_view, name='verbrauch'),
    path('cockpit/', views.cockpit_view, name='cockpit'),
    path('annual-electricity/', views.annual_electricity_view, name='annual_electricity'),
    path('smard/', views.smard_solar_wind, name='smard_solar_wind'),
    path('bilanz/', views.bilanz_view, name='bilanz'),
    path('api/balance-energy/', views.balance_energy, name='balance_energy'),
    path('api/balance-energy-lu6/', views.balance_energy_lu6, name='balance_energy_lu6'),
    path('api/ws/balance/', views.balance_ws_storage, name='balance_ws_storage'),
    path('api/balance-full/', views.balance_full_system, name='balance_full_system'),
    path('api/balance-all/', views.balance_all, name='balance_all'),
    # path('usecase-diagram/', views.usecase_diagram, name='usecase_diagram'),  # Disabled - view not implemented
    
    # API Endpoints
    path('api/update-user-percent/', views.update_user_percent, name='update_user_percent'),
    path('api/update/<str:code>/', views.update_user_percent, name='update_user_percent_code'),
    path('api/save-all-inputs/', views.save_all_user_inputs, name='save_all_inputs'),
    path('api/run-full-recalc/', views.run_full_recalc_view, name='run_full_recalc'),
    path('api/recalc-verbrauch/', views.recalc_verbrauch_view, name='recalc_verbrauch'),
    path('api/recalc-ws-formulas/', views.recalc_ws_formulas_view, name='recalc_ws_formulas'),
    path('api/update-verbrauch-bulk/', views.update_verbrauch_bulk, name='update_verbrauch_user_percent_bulk'),
    path('api/save-recalc-verbrauch/', views.save_and_recalculate_verbrauch, name='save_recalc_verbrauch'),
    path('api/save-verbrauch-user-input/', views.save_verbrauch_user_input, name='save_verbrauch_user_input'),
    path('api/unified-recalc/', views.unified_recalc_view, name='unified_recalc'),
    
    # Baseline Backup Management
    path('api/baseline/create/', views.create_baseline, name='create_baseline'),
    path('api/baseline/restore/', views.restore_baseline, name='restore_baseline'),
    path('api/baseline/info/', views.get_baseline_info, name='get_baseline_info'),
]
