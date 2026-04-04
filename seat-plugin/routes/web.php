<?php

use Illuminate\Support\Facades\Route;
use Volley\SeatVolley\Http\Controllers\VolleyController;

Route::middleware(['web', 'auth'])
    ->prefix('volley')
    ->group(function () {
        Route::get('/', [VolleyController::class, 'index'])->name('volley.index');
        Route::post('/calculate', [VolleyController::class, 'calculate'])->name('volley.calculate');
    });
