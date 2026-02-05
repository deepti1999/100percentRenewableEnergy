# Energy breakdown
total_load = 1389797  # GWh
wind = 706237  # GWh
water = 50000  # GWh  
bio = 30000  # GWh
storage_losses = 33919  # GWh

# Residual that solar must cover
must_cover = total_load + storage_losses - wind - water - bio
print(f'Total demand + losses: {total_load + storage_losses:,} GWh')
print(f'Wind + Water + Bio:    {wind + water + bio:,} GWh')
print(f'Residual for Solar:    {must_cover:,} GWh')

# Solar energy actually produced
solar_actual = 637479
print(f'Solar actual:          {solar_actual:,} GWh')

# Land calculation
solar_yield = 1235  # MWh/ha/year
current_land = solar_actual * 1000 / solar_yield
target_land = 700000
target_solar = target_land * solar_yield / 1000

print(f'\nCurrent solar land:    {current_land:,.0f} ha')
print(f'Target solar land:     {target_land:,.0f} ha')
print(f'For 700k ha, need:     {target_solar:,.0f} GWh solar')
print(f'Additional solar:      {target_solar - solar_actual:,.0f} GWh')
