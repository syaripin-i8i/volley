<?php

return [
    'volley' => [
        'name'          => 'Damage Calc',
        'icon'          => 'fas fa-crosshairs',
        'route_segment' => 'volley',
        'permission'    => 'volley.view',
        'entries'       => [
            [
                'name'       => 'Calculator',
                'icon'       => 'fas fa-calculator',
                'route'      => 'volley.index',
                'permission' => 'volley.view',
            ],
        ],
    ],
];
